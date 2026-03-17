import os
from dotenv import load_dotenv

load_dotenv()

# Nextcloud Configuration
NEXTCLOUD_URL = os.getenv("NEXTCLOUD_URL")
NEXTCLOUD_USERNAME = os.getenv("NEXTCLOUD_USERNAME")
NEXTCLOUD_PASSWORD = os.getenv("NEXTCLOUD_PASSWORD")
WATCH_DIRECTORY = os.getenv("WATCH_DIRECTORY", "Öffentlichkeitsarbeit")

# GitHub Configuration 
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_REPO_NAME = os.getenv("GITHUB_REPO_NAME") # e.g. "owner/repo"
GITHUB_BRANCH = os.getenv("GITHUB_BRANCH", "main")

# Hugo Configuration
HUGO_REPO_URL = os.getenv("HUGO_REPO_URL")

# General Configuration
LOGLEVEL = os.getenv("LOGLEVEL", "INFO")
INTERVAL = os.getenv("INTERVAL", 3600)