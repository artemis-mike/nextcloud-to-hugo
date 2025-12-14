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
    year_directories = []
    reYear = re.compile(r'^\d{4}$')
    try:
        for node in nc.files.listdir(directory):
            if node.is_dir and reYear.match(node.name):
                year_directories.append(node.name)
                logging.debug(f"Found year directory: {node.name}")
        
        logging.info(f"Found {len(year_directories)} year directories: {sorted(year_directories)}")
        return sorted(year_directories)
    except Exception as e:
        logging.error(f"Error getting year directories from '{directory}': {e}")
        return []


def getDirectoriesByYear(watch_directory, year_directories):
    """
    Get all subdirectories organized by year.
    
    Args:
        watch_directory: The base directory to search in
        year_directories: List of year directory names (e.g., ['2021', '2022', ...])
        
    Returns:
        dict: Dictionary mapping year (str) -> list of directory names (list of str)
              Example: {'2021': ['Friedenslicht', 'Insektenhotel', ...], 
                       '2022': ['07.04. Kerzen basteln', ...], ...}
    """
    directories_by_year = {}
    
    for year in year_directories:
        year_path = f"{watch_directory}/{year}"
        directories_by_year[year] = []
        
        try:
            for node in nc.files.listdir(year_path):
                if node.is_dir:
                    directories_by_year[year].append(node.name)
                    logging.debug(f"Found directory: {year}: {node.name}")
            
            logging.info(f"Found {len(directories_by_year[year])} directories for year {year}")
        except Exception as e:
            logging.error(f"Error getting directories for year {year}: {e}")
    
    return directories_by_year


# Get year directories
years_directories = getYearDirectories(WATCH_DIRECTORY)
logging.info(f"Year directories: {years_directories}")

# Get all subdirectories organized by year
directories_by_year = getDirectoriesByYear(WATCH_DIRECTORY, years_directories)

# Example: Loop through all directories of a given year
example_year = "2024"
if example_year in directories_by_year:
    logging.info(f"Directories for year {example_year}:")
    for dir_name in directories_by_year[example_year]:
        logging.info(f"  - {dir_name}")

# Example: Loop through all years and their directories
logging.info("All directories by year:")
for year, dirs in directories_by_year.items():
    logging.info(f"Year {year}: {len(dirs)} directories")
    for dir_name in dirs:
        logging.debug(f"  - {dir_name}")

sys.exit(0)