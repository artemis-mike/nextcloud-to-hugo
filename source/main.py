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


def parse_date_from_directory_name(dir_name, default_year):
    """
    Parse a date from a directory name and return it in ISO format (YYYY-MM-DD).
    Always extracts the START date from date ranges.
    
    Handles various formats:
    - "07.04. Kerzen basteln" -> 2022-04-07 (uses default_year)
    - "13.01.2024 Christbaumsammlung" -> 2024-01-13
    - "19.-21.04.2024" -> 2024-04-19 (takes start date from range)
    - "19. - 25.05.2024 Zeltlager" -> 2024-05-19 (takes start date from range)
    - "05-10.08." -> 2024-08-05 (takes start date, uses default_year)
    - "30.04. - 04.05. Pilsen-Wenzenbach" -> 2024-04-30 (takes start date)
    
    Args:
        dir_name: Directory name string
        default_year: Year to use if not found in directory name (str or int)
        
    Returns:
        str: Date in ISO format (YYYY-MM-DD) or None if no date found
    """
    # Convert default_year to string
    default_year = str(default_year)
    
    # Pattern 1: Single date without year: DD.MM. (at start of string or after space)
    # Examples: "07.04. Kerzen basteln"
    pattern1_single = re.compile(r'(?:^|\s)(\d{1,2})\.(\d{1,2})\.(?!\d)')
    match1_single = pattern1_single.search(dir_name)
    if match1_single:
        day, month = match1_single.groups()
        try:
            date_obj = datetime(int(default_year), int(month), int(day))
            return date_obj.strftime('%Y-%m-%d')
        except ValueError:
            pass

    # Pattern 2: Date range with full year: DD-DD.MM.YYYY or DD.-DD.MM.YYYY or DD. - DD.MM.YYYY
    # Examples: "19.-21.04.2024", "19. - 25.05.2024", "06. - 08.06.2025"
    # Must have a dot after the first day to ensure we capture the START date
    pattern2_range = re.compile(r'(\d{1,2})\.\s*[-.]\s*\d{1,2}\.(\d{1,2})\.(\d{4})')
    match2_range = pattern2_range.search(dir_name)
    if match2_range:
        start_day, month, year = match2_range.groups()
        try:
            date_obj = datetime(int(year), int(month), int(start_day))
            return date_obj.strftime('%Y-%m-%d')
        except ValueError:
            pass
    
    # Pattern 3: Date range without year: DD-DD.MM. or DD.-DD.MM. or DD. - DD.MM.
    # Examples: "05-10.08.", "30.04. - 04.05."
    # Must have a dot after the first day to ensure we capture the START date
    pattern3_range = re.compile(r'(\d{1,2})\.\s*[-.]\s*\d{1,2}\.(\d{1,2})\.')
    match3_range = pattern3_range.search(dir_name)
    if match3_range:
        start_day, month = match3_range.groups()
        try:
            date_obj = datetime(int(default_year), int(month), int(start_day))
            return date_obj.strftime('%Y-%m-%d')
        except ValueError:
            pass
    
    # Pattern 4: Single date with full year: DD.MM.YYYY
    pattern4_single = re.compile(r'(\d{1,2})\.(\d{1,2})\.(\d{4})')
    match4_single = pattern4_single.search(dir_name)
    if match4_single:
        day, month, year = match4_single.groups()
        try:
            date_obj = datetime(int(year), int(month), int(day))
            return date_obj.strftime('%Y-%m-%d')
        except ValueError:
            pass
    

    
    return None


def getArticlesByYear(watch_directory, year_directories):
    """
    Get all subdirectories organized by year with date information.
    
    Args:
        watch_directory: The base directory to search in
        year_directories: List of year directory names (e.g., ['2021', '2022', ...])
        
    Returns:
        dict: Dictionary mapping year (str) -> list of article dicts
              Each article dict has:
              - 'name': directory name (str)
              - 'date': date in ISO format YYYY-MM-DD (str or None)
              
              Example: {
                  '2022': [
                      {'name': '07.04. Kerzen basteln', 'date': '2022-04-07'},
                      {'name': '13.01.2024 Christbaumsammlung', 'date': '2024-01-13'},
                      ...
                  ],
                  ...
              }
    """
    articles_by_year = {}
    
    for year in year_directories:
        year_path = f"{watch_directory}/{year}"
        articles_by_year[year] = []
        
        try:
            for node in nc.files.listdir(year_path):
                if node.is_dir:
                    # Parse date from directory name
                    date_str = parse_date_from_directory_name(node.name, year)
                    
                    article = {
                        'name': node.name,
                        'date': date_str
                    }
                    articles_by_year[year].append(article)
                    
                    if date_str:
                        logging.debug(f"Found directory: {year}: {node.name} -> {date_str}")
                    else:
                        logging.debug(f"Found directory: {year}: {node.name} -> (no date)")
            
            logging.info(f"Found {len(articles_by_year[year])} directories for year {year}")
        except Exception as e:
            logging.error(f"Error getting directories for year {year}: {e}")
    
    return articles_by_year

def cleanup_article(articles):
    """
    Placeholder for article cleanup/processing function.
    """
    pass


# Get year directories
years_directories = getYearDirectories(WATCH_DIRECTORY)
logging.info(f"Year directories: {years_directories}")

# Get all subdirectories organized by year
articles_by_year = getArticlesByYear(WATCH_DIRECTORY, years_directories)

# # Example: Loop through all directories of a given year
# example_year = "2024"
# if example_year in articles_by_year:
#     logging.info(f"Directories for year {example_year}:")
#     for article in articles_by_year[example_year]:
#         if article['date']:
#             logging.info(f"  - {article['name']} (date: {article['date']})")
#         else:
#             logging.info(f"  - {article['name']} (no date)")


for year in years_directories:
    logging.info(f"Directories for year {year}:")
    for article in articles_by_year[year]:
        if article['date']:
            logging.info(f"  - {article['name']} (date: {article['date']})")
        else:
            logging.info(f"  - {article['name']} (no date)")

# # Example: Loop through all years and their directories
# logging.info("All directories by year:")
# for year, articles in articles_by_year.items():
#     logging.info(f"Year {year}: {len(articles)} directories")
#     for article in articles:
#         if article['date']:
#             logging.debug(f"  - {article['name']} -> {article['date']}")
#         else:
#             logging.debug(f"  - {article['name']} -> (no date)")

sys.exit(0)