#import pandas as pd
import requests
import time
import json
from datetime import datetime

headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
            ' AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36'
        }

url = 'https://api.tfl.gov.uk/BikePont/'
timeout = 10
num_tries = 3
wait_time = 5
retry_status_codes = [408, 500]

def _save_file(data: json, today: datetime):
    file_path = f'data/bike_data_{today.strftime("%Y_%m_%d_T%H-%M-%S")}.json'
    with open(file_path, 'w') as file:
        json.dump(data, file)
    return file_path

def _api_call():
    response = requests.get(url, headers=headers, timeout=timeout)

    if response.status_code == 200:
        today = datetime.today()
        today_json = {'today' : str(today)}
        try:
            response_json = response.json()
        except:
            raise Exception('File is not a json') # stops retries
        for bikepoint in response_json:
            bikepoint.update(today_json)
        return response_json, today
    elif response.status_code in retry_status_codes:
        raise Exception(f'API error: status code {response.reason}') # retry
    else:
        raise Exception(f'Not retrying due to some other error: {response.reason} - {response.status_code}') # stops retries

def api_call_with_retries():    

    """ main function to call the API and save returned JSON. 
    Under certain response status errors, will retry after waiting.
    Else, will raise exception and stop retrying."""
    
    for attempt in range(1, num_tries + 1):
        try:
            data, today = _api_call()
            file_path = _save_file(data, today)
            # need to add logging
            print(f'Successfully saved data into {file_path}')
            return data
        except Exception as e:
            print(f'Attempt {attempt} failed: {e}')
            if str(e) == 'File is not a json' or str(e).startswith('Not retrying due to some other error'):
                # need to add logging
                print(e)
                break
            elif attempt < num_tries:
                # need to add logging
                print(f'Retrying in {wait_time} seconds...')
                time.sleep(wait_time)
            else:
                # need to add logging
                raise Exception(f'Failed to connect after multiple attempts')

data = api_call_with_retries()







