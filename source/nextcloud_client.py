import logging
from nc_py_api import Nextcloud
import re
from datetime import datetime

class NextcloudClient:
    def __init__(self, url, username, password):
        self.url = url
        self.username = username
        self.password = password
        self.nc = None

    def connect(self):
        logging.info(f"Connecting to Nextcloud at: {self.url}")
        try:
            self.nc = Nextcloud(nextcloud_url=self.url, nc_auth_user=self.username, nc_auth_pass=self.password)
            user_info = self.nc.user
            logging.debug(f"Authenticated as user: {user_info}")
            return True
        except Exception as e:
            logging.error(f"Failed to connect to Nextcloud: {e}")
            return False

    def get_year_directories(self, directory):
        year_directories = []
        reYear = re.compile(r'^\d{4}$')
        try:
            for node in self.nc.files.listdir(directory):
                if node.is_dir and reYear.match(node.name):
                    year_directories.append(node.name)
            
            logging.info(f"Found {len(year_directories)} year directories: {sorted(year_directories)}")
            return sorted(year_directories)
        except Exception as e:
            logging.error(f"Error getting year directories from '{directory}': {e}")
            return []

    def parse_date_from_directory_name(self, dir_name, default_year):
        default_year = str(default_year)
        
        # Pattern 1
        pattern1_single = re.compile(r'(?:^|\s)(\d{1,2})\.(\d{1,2})\.(?!\d)')
        match1_single = pattern1_single.search(dir_name)
        if match1_single:
            day, month = match1_single.groups()
            try:
                date_obj = datetime(int(default_year), int(month), int(day))
                return date_obj.strftime('%Y-%m-%d')
            except ValueError:
                pass

        # Pattern 2
        pattern2_range = re.compile(r'(\d{1,2})\.\s*[-.]\s*\d{1,2}\.(\d{1,2})\.(\d{4})')
        match2_range = pattern2_range.search(dir_name)
        if match2_range:
            start_day, month, year = match2_range.groups()
            try:
                date_obj = datetime(int(year), int(month), int(start_day))
                return date_obj.strftime('%Y-%m-%d')
            except ValueError:
                pass
        
        # Pattern 3
        pattern3_range = re.compile(r'(\d{1,2})\.\s*[-.]\s*\d{1,2}\.(\d{1,2})\.')
        match3_range = pattern3_range.search(dir_name)
        if match3_range:
            start_day, month = match3_range.groups()
            try:
                date_obj = datetime(int(default_year), int(month), int(start_day))
                return date_obj.strftime('%Y-%m-%d')
            except ValueError:
                pass
        
        # Pattern 4
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

    def get_articles_by_year(self, watch_directory, year_directories):
        articles_by_year = {}
        for year in year_directories:
            year_path = f"{watch_directory}/{year}"
            articles_by_year[year] = []
            
            try:
                for node in self.nc.files.listdir(year_path):
                    if node.is_dir:
                        date_str = self.parse_date_from_directory_name(node.name, year)
                        
                        article = {
                            'name': node.name,
                            'date': date_str,
                            'path': f"{year_path}/{node.name}"
                        }
                        articles_by_year[year].append(article)
            except Exception as e:
                logging.error(f"Error getting directories for year {year}: {e}")
        
        return articles_by_year

    def get_files_in_directory(self, directory_path):
        """Returns a list of files in a specific directory on Nextcloud."""
        try:
            return [node for node in self.nc.files.listdir(directory_path) if not node.is_dir]
        except Exception as e:
            logging.error(f"Error listing files in '{directory_path}': {e}")
            return []

    def download_file(self, remote_path, local_path):
        """Downloads a file from Nextcloud to a local path."""
        try:
            self.nc.files.download2stream(remote_path, local_path)
            logging.debug(f"Downloaded {remote_path} to {local_path}")
            return True
        except Exception as e:
            logging.error(f"Failed to download {remote_path}: {e}")
            return False
