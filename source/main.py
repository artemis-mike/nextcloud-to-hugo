import os
import shutil
import logging
import time
from config import (
    LOGLEVEL, NEXTCLOUD_URL, NEXTCLOUD_USERNAME, NEXTCLOUD_PASSWORD, WATCH_DIRECTORY,
    GITHUB_TOKEN, GITHUB_REPO_NAME, GITHUB_BRANCH, HUGO_REPO_URL
)
from nextcloud_client import NextcloudClient
from github_client import GithubClient
from hugo_generator import HugoGenerator
from document_parser import DocumentParser
import re

logging.basicConfig(format='%(asctime)s %(levelname)s\t%(message)s', encoding='utf-8')
logging.getLogger().setLevel(LOGLEVEL)

def replace_umlauts(text):
    text = text.replace('Ä', 'Ae').replace('Ö', 'Oe').replace('Ü', 'Ue')
    return text.replace('ä', 'ae').replace('ö', 'oe').replace('ü', 'ue').replace('ß', 'ss')

def clean_title(name):
    name_clean = re.sub(r'^(\d{2,4}[-_\.]\d{2,4}[-_\.]\d{2,4}[-_\. ]*)+', '', name)
    name_clean = re.sub(r'^(\d{2}[-_\.]\d{2}[-_\. ]*)+', '', name_clean)
    return name_clean.strip(' ._-')

def sanitize_branch_name(date, name):
    name = replace_umlauts(name)
    # Remove any leading date-like structures from the name
    # Matches: DD.MM., DD-MM, YYYY-MM-DD, DD.MM.YYYY, 03_09__ etc
    name_clean = re.sub(r'^(\d{2,4}[-_\.]\d{2,4}[-_\.]\d{2,4}[-_\. ]*)+', '', name)
    name_clean = re.sub(r'^(\d{2}[-_\.]\d{2}[-_\. ]*)+', '', name_clean)
    # Replace non-alphanumeric with hyphen
    target = re.sub(r'[^a-zA-Z0-9]', '-', name_clean).lower()
    # Remove consecutive hyphens and strip
    target = re.sub(r'-+', '-', target).strip('-')
    return f'add-post-{date}-{target[:40].strip("-")}'

def sanitize_dir_name(date, name):
    name = replace_umlauts(name)
    # Remove any leading date-like structures from the name
    name_clean = re.sub(r'^(\d{2,4}[-_\.]\d{2,4}[-_\.]\d{2,4}[-_\. ]*)+', '', name)
    name_clean = re.sub(r'^(\d{2}[-_\.]\d{2}[-_\. ]*)+', '', name_clean)
    # Replace anything that isn't alphanumeric with an underscore
    name_clean = re.sub(r'[^a-zA-Z0-9]', '_', name_clean)
    # Remove consecutive underscores and strip leading/trailing underscores
    name_clean = re.sub(r'_+', '_', name_clean).strip('_')
    
    return f"{date}_{name_clean}".lower()

def main():
    while True:
        if not all([NEXTCLOUD_URL, NEXTCLOUD_USERNAME, NEXTCLOUD_PASSWORD, GITHUB_TOKEN, GITHUB_REPO_NAME, HUGO_REPO_URL]):
            logging.error("Missing required environment variables (Nextcloud, GitHub, or Hugo repo).")
            return
        
        f = open("./lastRun.epoch", "w")     # Relevant for health.sh / health-compose.sh
        f.write(str(round(datetime.now().timestamp())))
        f.close()

        nc_client = NextcloudClient(NEXTCLOUD_URL, NEXTCLOUD_USERNAME, NEXTCLOUD_PASSWORD)
        if not nc_client.connect():
            return
            
        gh_client = GithubClient(GITHUB_TOKEN, GITHUB_REPO_NAME)
        if not gh_client.connect():
            return

        tmp_workspace = os.path.join(os.getcwd(), "tmp_workspace")
        hugo_gen = HugoGenerator(tmp_workspace, HUGO_REPO_URL, token=GITHUB_TOKEN)
        
        if not hugo_gen.clone_or_open_repo():
            return

        year_dirs = nc_client.get_year_directories(WATCH_DIRECTORY)
        articles_by_year = nc_client.get_articles_by_year(WATCH_DIRECTORY, year_dirs)

        valid_branch_names = []
        
        # Sort years in reverse order (youngest first)
        sorted_years = sorted(articles_by_year.keys(), reverse=True)

        for year in sorted_years:
            articles = articles_by_year[year]
            logging.info(f"Working on year directory {year}")
            
            # Sort articles by date in reverse (youngest first)
            sorted_articles = sorted(articles, key=lambda x: x['date'] if x['date'] else "", reverse=True)
            
            for article in sorted_articles:
                if not article['date']:
                    logging.warning(f"Skipping {article['name']} because no date was parsed.")
                    continue

                # Switch back to main just in case we are on another branch from a previous failure
                hugo_gen.repo.git.checkout(GITHUB_BRANCH)

                dir_name_clean = sanitize_dir_name(article['date'], article['name'])
                branch_name = sanitize_branch_name(article['date'], article['name'])
                
                if hugo_gen.check_if_exists_in_hugo(year, dir_name_clean):
                    logging.info(f"Article {article['name']} already exists in Hugo repo.")
                    valid_branch_names.append(branch_name)
                    continue
                    
                if gh_client.has_open_pr(branch_name):
                    logging.info(f"Open PR already exists for branch {branch_name}")
                    valid_branch_names.append(branch_name)
                    continue

                # Process Nextcloud Files
                logging.info(f"Processing new article: {article['name']}")
                article_tmp_dir = os.path.join(tmp_workspace, "downloads", dir_name_clean)
                os.makedirs(article_tmp_dir, exist_ok=True)
                
                files = nc_client.get_files_in_directory(article['path'])
                doc_file = None
                media_files = []
                
                for file_node in files:
                    remote_path = f"{article['path']}/{file_node.name}"
                    local_path = os.path.join(article_tmp_dir, file_node.name)
                    # Download file
                    nc_client.download_file(remote_path, local_path)
                    
                    if DocumentParser.is_supported(file_node.name):
                        doc_file = local_path
                    elif os.path.splitext(file_node.name)[1].lower() in ['.jpg', '.jpeg', '.png', '.gif']:
                        media_files.append(local_path)
                
                if not doc_file:
                    logging.warning(f"Skipping {article['name']} because no supported document (doc, docx, odt, txt, md) was found.")
                    continue
                    
                markdown_content = DocumentParser.parse_to_markdown(doc_file)
                
                # Setup Hugo Post Directory
                hugo_gen.create_branch(branch_name)
                
                hugo_post_dir = os.path.join(hugo_gen.repo_dir, "content", "post", str(year), dir_name_clean)
                os.makedirs(hugo_post_dir, exist_ok=True)
                
                # Move media files
                for m in media_files:
                    shutil.copy(m, os.path.join(hugo_post_dir, os.path.basename(m)))
                    
                # Resize images before creating index.md
                hugo_gen.resize_images(hugo_post_dir)
                    
                # Create index.md
                index_path = os.path.join(hugo_post_dir, "index.md")
                
                clean_name = clean_title(article['name'])
                title = clean_name
                date = article['date']
                image = os.path.basename(media_files[0]) if media_files else ""
                tags = "[]"
                categories = "[]"
                desc = ""
                
                frontmatter = (
                    "---\n"
                    f"title: '{title}'\n"
                    f"date: {date}T00:00:00+02:00\n"
                    "draft: false\n"
                )
                if image:
                    frontmatter += f"image: {image}\n"
                
                frontmatter += (
                    f"tags: {tags}\n"
                    f"description: {desc}\n"
                    f"categories: {categories}\n"
                    "---\n\n"
                )
                
                with open(index_path, "w", encoding='utf-8') as f:
                    f.write(frontmatter + markdown_content)
                    
                # Commit and push
                if hugo_gen.commit_and_push(f"Add post {date} {title}", branch_name):
                    # Create PR
                    gh_client.create_pull_request(
                        title=f"(nextcloud-to-hugo) Add post: {date} {title}",
                        body="Automated PR created from Nextcloud directory.",
                        head_branch=branch_name,
                        base_branch=GITHUB_BRANCH
                    )
                
                valid_branch_names.append(branch_name)
                logging.info(f"Finished processing {article['name']}.")

        # Finally switch to main branch
        hugo_gen.repo.git.checkout(GITHUB_BRANCH)
        
        # Cleanup obsolete pull requests
        logging.info("Checking for obsolete Pull Requests...")
        open_bot_prs = gh_client.get_open_bot_prs()
        for pr in open_bot_prs:
            if pr.head.ref not in valid_branch_names:
                logging.warning(f"PR branch {pr.head.ref} is obsolete. Closing PR #{pr.number}.")
                gh_client.close_pull_request(pr.number)
                # Delete remote branch
                try:
                    origin = hugo_gen.repo.remote(name='origin')
                    # Passing empty string (None) as source explicitly deletes the destination ref
                    origin.push(f":{pr.head.ref}")
                    logging.info(f"Deleted remote branch {pr.head.ref} from origin.")
                except Exception as e:
                    logging.warning(f"Failed to delete remote branch {pr.head.ref}: {e}")
                    
        # Cleanup tmp directory downloads, we keep the hugo_blog to avoid recloning if we run it continuously
        shutil.rmtree(os.path.join(tmp_workspace, "downloads"), ignore_errors=True)

        logging.info("Finished. Sleeping for %ss.", INTERVAL)
        time.sleep(INTERVAL)

if __name__ == "__main__":
    main()