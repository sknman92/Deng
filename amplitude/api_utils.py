import requests
import json
from datetime import datetime
import dotenv
import os
import tempfile
import zipfile
import gzip

# loading AMP api keys
dotenv.load_dotenv()
AMP_API_KEY = os.getenv('AMP_API_KEY')
AMP_SECRET_KEY = os.getenv('AMP_SECRET_KEY')

# setting api variables
headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
            ' AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36'
        }

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

    file_path = f'data/{file_name}_{extract_time}.{file_type}'
    with open(file_path, 'wb') as file:
        file.write(response.content)
    
    # we want to return file path if needed for further processing
    return file_path

def _unzipping_response(file_path: str, file_name: str, extract_time: datetime):
    with tempfile.TemporaryDirectory() as temp_dir:
        with zipfile.ZipFile(file_path, 'r') as zip_ref:
            zip_ref.extractall(temp_dir)

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

        count = 1
        for file in file_list:
            with gzip.open(f'{parent_folder_path}/{file}', 'rt', encoding='UTF-8') as f:
                extract_time_str = {'extract_time': str(extract_time)}
                final_file_path = f'data/{file_name}_{extract_time}.json'
                with open(final_file_path, 'a', encoding='UTF-8') as final_file:
                    for line in f:
                        event = json.loads(line)
                        event.update(extract_time_str)
                        final_file.write(json.dumps(event) + '\n')
                        count += 1

    return count, final_file_path