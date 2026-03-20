import os
import shutil
import logging
import subprocess
from git import Repo
from datetime import datetime

class HugoGenerator:
    def __init__(self, workspace_dir, repo_url, token=None):
        self.workspace_dir = workspace_dir
        self.repo_url = repo_url
        self.token = token
        self.repo_dir = os.path.join(workspace_dir, "hugo_blog")
        self.repo = None

    def _get_authenticated_url(self):
        """Injects the token into the repository URL if provided."""
        if not self.token or not self.repo_url.startswith("https://"):
            return self.repo_url
        
        # Format: https://<token>@github.com/owner/repo.git
        return self.repo_url.replace("https://", f"https://{self.token}@")

    def clone_or_open_repo(self):
        """Clones the repository if it doesn't exist, otherwise opens it."""
        try:
            if not os.path.exists(self.repo_dir):
                auth_url = self._get_authenticated_url()
                logging.info(f"Cloning repository into {self.repo_dir}")
                self.repo = Repo.clone_from(auth_url, self.repo_dir)
            else:
                logging.info(f"Opening existing repository at {self.repo_dir}")
                self.repo = Repo(self.repo_dir)
                
                try:
                    # Fetch first, then reset hard to avoid pull conflicts with dirty working tree
                    origin = self.repo.remotes.origin
                    
                    # Update remote URL to include token if it changed or wasn't there
                    auth_url = self._get_authenticated_url()
                    origin.set_url(auth_url)
                    
                    origin.fetch()
                    
                    # If we were on a custom branch before, ensure we switch back to main/master tracking branch first
                    # The main script usually switches back, but if it crashed, we might be left in a dirty state.
                    # Try checkout main, then master if main doesn't exist
                    try:
                        self.repo.git.checkout('main')
                    except:
                        try:
                            self.repo.git.checkout('master')
                        except:
                            logging.warning("Could not checkout main or master branch before pulling.")
                    
                    self.repo.git.reset('--hard', 'origin/HEAD')
                    self.repo.git.clean('-fd')
                    
                    # Now it should be completely clean, we can pull safely
                    origin.pull()
                except Exception as git_e:
                    from git.exc import GitCommandError
                    if isinstance(git_e, GitCommandError):
                        logging.error(f"GitCommandError during pull: stdout:\n{git_e.stdout}\nstderr:\n{git_e.stderr}")
                    raise git_e
            
            # Disable hooks to prevent UnicodeDecodeError on Windows from WSL/bash hooks
            try:
                # We do not set hooks path to os.devnull anymore, because `git lfs install`
                # tries to create a directory or file there and fails if it is /dev/null
                
                # And aggressively delete the hooks directory just to be absolutely sure
                hooks_dir = os.path.join(self.repo_dir, '.git', 'hooks')
                if os.path.exists(hooks_dir):
                    shutil.rmtree(hooks_dir, ignore_errors=True)
            except Exception as e:
                logging.warning(f"Could not disable git hooks: {e}")

            # Setup Git LFS
            try:
                # Use --skip-repo to avoid creating hooks, or --force if needed
                self.repo.git.lfs('install', '--skip-repo')
                logging.info("Git LFS initialized locally without hooks.")
            except Exception as lfs_e:
                logging.error(f"Git LFS install failed (might not be installed on system): {lfs_e}")
                return False

            return True
        except Exception as e:
            logging.error(f"Failed to clone or open repo: {e}")
            return False

    def check_if_exists_in_hugo(self, year, dir_name):
        post_dir = os.path.join(self.repo_dir, "content", "post", str(year))
        if not os.path.exists(post_dir):
            return False
        
        # Normalize both strings by replacing hyphens with underscores to handle variations 
        # like stand-up-paddling vs stand_up_paddling
        normalized_dir_name = dir_name.lower().replace('-', '_')
        return any(normalized_dir_name in d.lower().replace('-', '_') for d in os.listdir(post_dir))

    def create_branch(self, branch_name):
        try:
            logging.info(f"Creating new branch: {branch_name}")
            self.repo.git.checkout('-B', branch_name)
            return True
        except Exception as e:
            logging.error(f"Failed to create branch {branch_name}: {e}")
            return False

    def commit_and_push(self, message, branch_name):
        try:
            # Add files to git lfs tracking explicitly
            self.repo.git.lfs('track', '*.jpg', '*.jpeg', '*.png', '*.JPG', '*.gif')
            
            self.repo.git.add(A=True)
            if not self.repo.index.diff("HEAD"):
                logging.info("Nothing to commit.")
                return False
                
            self.repo.index.commit(message)
            
            # Explicitly push LFS objects first, since we disabled the pre-push hook during install
            try:
                logging.info("Pushing Git LFS objects...")
                self.repo.git.lfs('push', 'origin', branch_name)
            except Exception as lfs_push_e:
                logging.warning(f"Git LFS push encountered an issue (can usually be ignored if no LFS files): {lfs_push_e}")

            origin = self.repo.remote(name='origin')
            push_info = origin.push(branch_name, force=True)
            
            # Check for push errors
            for info in push_info:
                if info.flags & info.ERROR:
                    logging.error(f"Push failed for {branch_name}: {info.summary}")
                    return False
                    
            logging.info(f"Pushed branch {branch_name} to origin.")
            return True
        except Exception as e:
            logging.error(f"Failed to commit and push: {e}")
            return False

    def resize_images(self, target_dir):
        """Executes the image resizing script on the target directory."""
        script_path = os.path.join(self.repo_dir, "tools", "resize_images.sh")
        if not os.path.exists(script_path):
            logging.error(f"Image resize script not found at {script_path}")
            return False
        
        try:
            # Ensure the script is executable
            os.chmod(script_path, 0o755)
            
            logging.info(f"Running image resize script on {target_dir}")
            result = subprocess.run([script_path, target_dir], capture_output=True, text=True)
            
            if result.returncode == 0:
                logging.info("Image resizing completed successfully.")
                logging.debug(f"Script output: {result.stdout}")
                return True
            else:
                logging.error(f"Image resizing failed with return code {result.returncode}")
                logging.error(f"Script stderr: {result.stderr}")
                return False
        except Exception as e:
            logging.error(f"Error executing resize script: {e}")
            return False

    def cleanup(self):
        """Removes the cloned repo directory."""
        if os.path.exists(self.repo_dir):
            try:
                shutil.rmtree(self.repo_dir, ignore_errors=True)
                logging.info("Cleaned up temporary workspace.")
            except Exception as e:
                logging.error(f"Failed to clean up workspace: {e}")
