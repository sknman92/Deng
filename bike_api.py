import pandas as pd
import requests
import time
import json
from datetime import date

headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36'
        }

url = 'https://api.tfl.gov.uk/BikePoint/'
timeout = 10
num_tries = 50
wait_time = 30

def _api_call():
    response = requests.get(url, headers=headers, timeout=timeout)
    
    if response.status_code == 200:
        print('Successfully connected')
        today = date.today()
        
        return response.json()
    else:
        raise Exception(f'API error: status code {response.status_code}')

def api_call_with_retries():

    for attempt in range(1, num_tries + 1):
        try:
            data = _api_call()
            return data
            break
        except Exception as e:
            print(f'Attempt {attempt} failed: {e}')
            if attempt < num_tries:
                print(f'Retrying in {wait_time} seconds...')
                time.sleep(wait_time)
            else:
                raise Exception(f'Failed to connect after {num_tries} attempts') from e

