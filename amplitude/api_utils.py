import requests
import json
from datetime import datetime
import dotenv
import os
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

# function for making amp call w. exception handling
def _amp_api_call(url, file_name, retry_status_codes=None, **kwargs):
    response = requests.get(url, headers=headers, 
                        params=kwargs, auth=(AMP_API_KEY, AMP_SECRET_KEY))
    if retry_status_codes == None:
        retry_status_codes = [408, 500]
    if response.status_code == 200:
        # saving response
        extract_time = f'{datetime.now().strftime("%Y_%m_%d_T%H-%M-%S")}'
        if url == 'https://analytics.eu.amplitude.com/api/2/events/list':
            file_type = 'json'
        else:
            file_type = 'zip'
        file_path = f'data/{file_name}_{extract_time}.{file_type}'
        #os.makedirs(file_path, exist_ok = True)
        with open(file_path, 'wb') as file:
            file.write(response.content)
        return file_path, extract_time
    elif response.status_code in retry_status_codes:
        raise Exception(f'API error: status code {response.reason}') # retry for certain status codes
    else:
        raise Exception(f'Not retrying due to some other error:{response.reason} - {response.status_code}') # stops retries
    
def _unzipping_amp_events(file_path: str, extract_time: datetime):
    extract_path = f'extracts/amp_data_extracted_{extract_time}'
    with zipfile.ZipFile(file_path, 'r') as zip_ref:
        zip_ref.extractall(extract_path)
    
    parent_folder = os.listdir(extract_path)
    parent_folder_paths = []
    for folder in parent_folder:
        parent_folder_path = extract_path + '/' + folder
        parent_folder_paths.append(parent_folder_path)
    sub_folders = []
    for parent_folder_path in parent_folder_paths:
        sub_folder = os.listdir(parent_folder_path)
        sub_folders.extend(sub_folder)

    # Add all json files to list    
    file_list = []
    for file in sub_folders:
        file_list.append(file)

    # looping through to write to one file
    count = 1
    for file in file_list:
        with gzip.open(f'{parent_folder_path}/{file}', 'rt', encoding = 'UTF-8') as f:
            # adding extract time
            extract_time = {'extract_time': str(extract_time)}
            final_file_path = 'data/amp_data_final.json'
            with open(f'{final_file_path}', 'a', encoding = 'UTF-8') as final_file:
                for line in f:
                    event = json.loads(line)
                    event.update(extract_time)
                    final_file.write(json.dumps(event) + '\n')
                    count += 1
    
    return count, final_file_path