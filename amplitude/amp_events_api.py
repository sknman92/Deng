import time
from datetime import datetime, timedelta, date
import os
import logging
from api_utils import _api_call, _saving_api_response, _unzipping_response
from load_utils import amp_data_load

# for reloading libs
import importlib
import api_utils
import load_utils
importlib.reload(api_utils)
importlib.reload(load_utils)

# logging config
logging.basicConfig(
    filename="amp.log",
    filemode = "a",
    format = "%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    level=logging.INFO)

logger = logging.getLogger()

# api config
num_tries = 3
wait_time = 5

# main function to call the API, unzip returned file into JSON, with retry logic
def main_api_call(start: str = None, end: str = None):
    for retry in range(1, num_tries+1):
        try:
            assert start is not None and end is not None, "Both start and end date should be provided"
            # if start and end is not provided, default to yesterday 9-10
            if start and end is None:
                yesterday = date.today() - timedelta(days=1)
                start = datetime.combine(yesterday, datetime.min.time()).replace(hour=9).strftime('%Y%m%dT%H')
                end =  datetime.combine(yesterday, datetime.min.time()).replace(hour=10).strftime('%Y%m%dT%H')
            response, extract_time = _api_call('https://analytics.eu.amplitude.com/api/2/export', start=start, end=end)
            file_name = 'events_data'
            file_path = _saving_api_response(response, file_name, extract_time)
            count = _unzipping_response(file_path, extract_time)
            logger.info(f'Saved {count} events for dt range {start} - {end}')
            print(f'Saved {count} events for dt range {start} - {end}')
            amp_data_load()
            logger.info(f'Successfully loaded to S3')
            break
        except Exception as e:
            error = str(e)
            if error.startswith('Not retrying due to some other error'):
                logger.error(e)
                print(e)
                break
            elif retry < num_tries:
                logger.info(f'Attempt {retry} failed: {e}. Retrying in {wait_time} seconds...')
                print(f'Attempt {retry} failed: {e}. Retrying in {wait_time} seconds...')
                time.sleep(wait_time)
            else:
                logger.error(Exception('Failed to connect after multiple attempts'))
                raise Exception(f'Failed to connect after multiple attempts')


if __name__ == '__main__':
    main_api_call(start = '20251105T16', end = '20251105T18')





