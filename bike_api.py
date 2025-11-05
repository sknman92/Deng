import pandas as pd
import requests
import time
import json
from datetime import datetime
import logging

headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36'
        }

url = 'https://api.tfl.gov.uk/BikePoint/'
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

    if response and response.status_code == 200:
        print('Successfully connected')
        today = datetime.today()
        today_json = {'today' : str(today)}
        try:
            response_json = response.json()
        except:
            raise Exception('File is not a json')
        for bikepoint in response_json:
            bikepoint.update(today_json)
        return response_json, today
    elif response.status_code in retry_status_codes:
        raise Exception(f'API error: status code {response.reason}')
    else:
        print('Failed to connect')
        

def api_call_with_retries():

    for attempt in range(1, num_tries + 1):
        try:
            data, today = _api_call()
            file_path = _save_file(data, today)
            print(f'Successfully saved data into {file_path}')
            return data
        except Exception as e:
            if e == 'File is not a json':
                break
            print(f'Attempt {attempt} failed: {e}')
            if attempt < num_tries:
                print(f'Retrying in {wait_time} seconds...')
                time.sleep(wait_time)
            else:
                raise Exception(f'Failed to connect after multiple attempts')
        except:
            print('Failed to connect')


data = api_call_with_retries()






