import time
from datetime import datetime, timedelta, date
import os
import logging
from api_utils import _api_call, _saving_api_response, _unzipping_response, retry_custom_exceptions
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

# main function to call the API, unzip returned file into JSON, with retry logic

@retry_custom_exceptions()
def main_api_call(start: str = None, end: str = None):
        
    assert start is not None and end is not None, "Both start and end date should be provided"
    # if start and end is not provided, default to yesterday 9-10
    if start and end is None:
        yesterday = date.today() - timedelta(days=1)
        start = datetime.combine(yesterday, datetime.min.time()).replace(hour=0).strftime('%Y%m%dT%H')
        end =  datetime.combine(yesterday, datetime.min.time()).replace(hour=23).strftime('%Y%m%dT%H')
    response, extract_time = _api_call('https://analytics.eu.amplitude.com/api/2/export', start=start, end=end)
    file_name = 'events_data'
    file_path = _saving_api_response(response, file_name, extract_time)
    count = _unzipping_response(file_path, extract_time)
    logger.info(f'Saved {count} events for dt range {start} - {end}')
    print(f'Saved {count} events for dt range {start} - {end}')
    amp_data_load()
    logger.info(f'Successfully loaded to S3')
            


if __name__ == '__main__':
    main_api_call(start = '20251105T09', end = '20251105T10')


