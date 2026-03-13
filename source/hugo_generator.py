import os
import shutil
import logging
from git import Repo
from datetime import datetime

class HugoGenerator:
    def __init__(self, workspace_dir, repo_url):
        self.workspace_dir = workspace_dir
        self.repo_url = repo_url
        self.repo_dir = os.path.join(workspace_dir, "hugo_blog")
        self.repo = None

    def clone_or_open_repo(self):
        """Clones the repository if it doesn't exist, otherwise opens it."""
        try:
            if not os.path.exists(self.repo_dir):
                logging.info(f"Cloning repository {self.repo_url} into {self.repo_dir}")
                self.repo = Repo.clone_from(self.repo_url, self.repo_dir)
            else:
                logging.info(f"Opening existing repository at {self.repo_dir}")
                self.repo = Repo(self.repo_dir)
                
                try:
                    # Fetch first, then reset hard to avoid pull conflicts with dirty working tree
                    origin = self.repo.remotes.origin
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
                # Set hooks path to devnull to avoid default hook execution
                self.repo.git.config('core.hooksPath', os.devnull)
                
                # And aggressively delete the hooks directory just to be absolutely sure
                hooks_dir = os.path.join(self.repo_dir, '.git', 'hooks')
                if os.path.exists(hooks_dir):
                    shutil.rmtree(hooks_dir, ignore_errors=True)
            except Exception as e:
                logging.warning(f"Could not disable git hooks: {e}")

            # Setup Git LFS
            try:
                self.repo.git.lfs('install')
                logging.info("Git LFS initialized locally.")
            except Exception as lfs_e:
                logging.warning(f"Git LFS install failed (might not be installed on system): {lfs_e}")

            return True
        except Exception as e:
            logging.error(f"Failed to clone or open repo: {e}")
            return False

    def check_if_exists_in_hugo(self, year, dir_name):
        post_dir = os.path.join(self.repo_dir, "content", "post", str(year))
        if not os.path.exists(post_dir):
            return False
        
        return any(dir_name.lower() in d.lower() for d in os.listdir(post_dir))

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
            origin = self.repo.remote(name='origin')
            origin.push(branch_name)
            logging.info(f"Pushed branch {branch_name} to origin.")
            return True
        except Exception as e:
            logging.error(f"Failed to commit and push: {e}")
            return False

    def cleanup(self):
        """Removes the cloned repo directory."""
        if os.path.exists(self.repo_dir):
            try:
                shutil.rmtree(self.repo_dir, ignore_errors=True)
                logging.info("Cleaned up temporary workspace.")
            except Exception as e:
                logging.error(f"Failed to clean up workspace: {e}")
