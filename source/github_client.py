import logging
from github import Github
from github import Auth

class GithubClient:
    def __init__(self, token, repo_name):
        self.auth = Auth.Token(token) if token else None
        self.g = Github(auth=self.auth) if self.auth else Github()
        self.repo_name = repo_name
        self.repo = None

    def connect(self):
        try:
            logging.info(f"Connecting to GitHub repo: {self.repo_name}")
            self.repo = self.g.get_repo(self.repo_name)
            logging.debug(f"Connected to repo: {self.repo.full_name}")
            return True
        except Exception as e:
            logging.error(f"Failed to connect to GitHub repo {self.repo_name}: {e}")
            return False

    def has_open_pr(self, branch_name):
        """Checks if there is an open PR from the given branch."""
        try:
            pulls = self.repo.get_pulls(state='open', head=f"{self.repo.owner.login}:{branch_name}")
            return pulls.totalCount > 0
        except Exception as e:
            logging.error(f"Error checking open PRs for branch {branch_name}: {e}")
            return False

    def create_pull_request(self, title, body, head_branch, base_branch="main"):
        """Creates a Pull Request."""
        try:
            # GitHub API often requires the head branch to be namespaced with the username
            head_namespaced = f"{self.repo.owner.login}:{head_branch}"
            pr = self.repo.create_pull(
                title=title,
                body=body,
                head=head_namespaced,
                base=base_branch
            )
            logging.info(f"Created Pull Request: {pr.html_url}")
            return pr
        except Exception as e:
            logging.error(f"Failed to create Pull Request: {e}")
            return None
