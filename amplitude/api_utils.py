import requests
import json
from datetime import datetime
import dotenv
import os
import tempfile
import zipfile
import gzip
import time
import logging

# setting logger
# logging config
logging.basicConfig(
    filename="amp.log",
    filemode = "a",
    format = "%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    level=logging.INFO)

logger = logging.getLogger()


# loading AMP api keys
dotenv.load_dotenv()
AMP_API_KEY = os.getenv('AMP_API_KEY')
AMP_SECRET_KEY = os.getenv('AMP_SECRET_KEY')

# setting api variables
headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
            ' AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36'
        }

# retry decorator
def retry_custom_exceptions(retries = 3, sleep = 5):
    def decorator(func):
        def wrapper(*args, **kwargs):
            for i in range(1, retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    error = str(e)
                    if error.startswith('Not retrying due to some other error'):
                        logger.error(e)
                        print(e)
                        break
                    elif i < retries:
                        logger.info(f'Attempt {i} failed: {e}. Retrying in {sleep} seconds...')
                        print(f'Attempt {i} failed: {e}. Retrying in {sleep} seconds...')
                        time.sleep(sleep)
                    else:
                        logger.error(Exception('Failed to connect after multiple attempts'))
                        raise Exception(f'Failed to connect after multiple attempts')
        return wrapper
    return decorator

def _api_call(url: str, retry_status_codes=None, **kwargs):
    # function for making amp call w. raising custom exceptions
    extract_time = f'{datetime.now().strftime("%Y_%m_%d_T%H-%M-%S")}'
    response = requests.get(url, headers=headers, 
                        params=kwargs, auth=(AMP_API_KEY, AMP_SECRET_KEY))
    if retry_status_codes == None:
        retry_status_codes = [408, 500]
    if response.status_code == 200:
        print(f'Successfully connected to api')
        return response, extract_time
    elif response.status_code in retry_status_codes:
        raise Exception(f'API error: status code {response.reason}') # maybe retry for certain status codes
    else:
        raise Exception(f'Critical error:{response.reason} - {response.status_code}') # unspecified error - retrying may not help

def _saving_api_response(response, file_name: str, extract_time: datetime):
    # detecting file type and saving response
    content_type = response.headers.get('Content-Type', '').lower()
    if 'application/json' in content_type:
        file_type = 'json'
    elif 'application/zip' in content_type:
        file_type = 'zip'
    elif 'text/csv' in content_type:
        file_type = 'csv'

    if file_type == 'zip':
        file_path = f'data/zip/{file_name}_{extract_time}.{file_type}'
    elif file_type == 'json':
        file_path = f'data/list_data.{file_type}'
    with open(file_path, 'wb') as file:
        file.write(response.content)
    
    # we want to return file path if needed for further processing
    return file_path

def _unzipping_response(file_path: str, extract_time: datetime):
    # unzipping and extract repsonse for amp events zip file
    
    # we want to extract zip to a temp dir
    with tempfile.TemporaryDirectory() as temp_dir:
        with zipfile.ZipFile(file_path, 'r') as zip_ref:
            zip_ref.extractall(temp_dir)

        # we want to loop through all folders in extracted zip folder
        parent_folder = os.listdir(temp_dir)
        parent_folder_paths = []
        for folder in parent_folder:
            parent_folder_path = temp_dir + '/' + folder
            parent_folder_paths.append(parent_folder_path)

        sub_folders = []
        for parent_folder_path in parent_folder_paths:
            sub_folder = os.listdir(parent_folder_path)
            sub_folders.extend(sub_folder)

        file_list = []
        for file in sub_folders:
            file_list.append(file)

        # counting the number of rows extracted
        count = 0
        for file in file_list:
            file_path = f'{parent_folder_path}/{file}'
            with gzip.open(file_path, 'rt', encoding='UTF-8') as f:
                extract_time_str = {'extract_time': str(extract_time)}
                with open(f'data/{file}.json', 'a', encoding='UTF-8') as final_file:
                    for line in f:
                        event = json.loads(line)
                        # we want to update each line to include extract time
                        event.update(extract_time_str)
                        final_file.write(json.dumps(event) + '\n')
                        count += 1

    return count