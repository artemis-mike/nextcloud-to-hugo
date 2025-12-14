import requests
import git
import signal
import logging
import sys
import os
from json import dumps
from datetime import datetime
from nc_py_api import Nextcloud
from dotenv import load_dotenv
import re



NEXTCLOUD_URL = os.getenv("NEXTCLOUD_URL")
NEXTCLOUD_USERNAME = os.getenv("NEXTCLOUD_USERNAME")
NEXTCLOUD_PASSWORD = os.getenv("NEXTCLOUD_PASSWORD")
WATCH_DIRECTORY = os.getenv("WATCH_DIRECTORY", "Öffentlichkeitsarbeit")
LOGLEVEL = os.getenv("LOGLEVEL", "INFO")

logging.basicConfig(format='%(asctime)s %(levelname)s\t%(message)s', encoding='utf-8')
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
logging.getLogger().setLevel(LOGLEVEL)

def signal_handler(sig, frame):
  logging.info("Recevied signal " + str((signal.Signals(sig).name)) + ". Shutting down.")
  sys.exit(0)


# Validate that all required environment variables are set
if not NEXTCLOUD_URL:
    logging.error("NEXTCLOUD_URL environment variable is not set")
    sys.exit(1)
if not NEXTCLOUD_USERNAME:
    logging.error("NEXTCLOUD_USERNAME environment variable is not set")
    sys.exit(1)
if not NEXTCLOUD_PASSWORD:
    logging.error("NEXTCLOUD_PASSWORD environment variable is not set")
    sys.exit(1)

logging.info(f"Connecting to Nextcloud at: {NEXTCLOUD_URL}")
logging.debug(f"Username: {NEXTCLOUD_USERNAME}")
logging.debug(f"Password: {'*' * len(NEXTCLOUD_PASSWORD) if NEXTCLOUD_PASSWORD else 'NOT SET'}\n")

try:
    nc = Nextcloud(nextcloud_url=NEXTCLOUD_URL, nc_auth_user=NEXTCLOUD_USERNAME, nc_auth_pass=NEXTCLOUD_PASSWORD)
    pretty_capabilities = dumps(nc.capabilities, indent=2, sort_keys=True)
    logging.debug("Capabilities retrieved successfully:")
    logging.debug(pretty_capabilities)
    
    # Test authentication by trying to get user info
    # This might fail with 401 if credentials are wrong, but capabilities worked
    try:
        user_info = nc.user
        logging.debug(f"Authenticated as user: {user_info}")
        logging.debug("Authentication successful!")
    except Exception as user_error:
        logging.warning(f"Could not retrieve user info: {user_error}")
except Exception as e:
    logging.error(f"Failed to connect to Nextcloud: {e}")
    sys.exit(1)

def getYearDirectories(directory):
    """
    Get a list of directories that are named like YYYY (4-digit years).
    
    Args:
        directory: The directory path to search in
        
    Returns:
        list: List of year directory names (strings)
    """
    yearDirectories = []
    reYear = re.compile(r'^\d{4}$')
    
    try:
        for node in nc.files.listdir(directory):
            if node.is_dir and reYear.match(node.name):
                yearDirectories.append(node.name)
                logging.debug(f"Found year directory: {node.name}")
        
        logging.info(f"Found {len(yearDirectories)} year directories: {sorted(yearDirectories)}")
        return sorted(yearDirectories)
    except Exception as e:
        logging.error(f"Error getting year directories from '{directory}': {e}")
        return []


yearsDirectories = getYearDirectories(WATCH_DIRECTORY)
logging.info(f"Year directories: {yearsDirectories}")

sys.exit(0)