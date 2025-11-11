import time
from datetime import datetime, timedelta, date
import os
import logging
from api_utils import _api_call, _saving_api_response, _unzipping_response
from load_utils import amp_data_load, return_s3_files, pull_missing_events

# logging config
logging.basicConfig(
    filename="amp.log",
    filemode = "a",
    format = "%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    level=logging.INFO)

logger = logging.getLogger()

def amp_retry_function():
    # returning all s3 files
    files = return_s3_files()

    # creating ranges of missing data
    ranges = pull_missing_events(files)
    
    # if missing ranges, loop through, retrive, and re-upload
    if ranges:
        logger.info(f'Missing data: {ranges}')
        for r in ranges:
            try:
                start = r.get('start', '')
                end = r.get('end', '')
                response, extract_time = _api_call('https://analytics.eu.amplitude.com/api/2/export', start=start, end=end)
                file_path = _saving_api_response(response, 'events_data', extract_time)
                count = _unzipping_response(file_path, extract_time)
                logger.info(f'Saved {count} events for dt range {start} - {end}')
                print(f'Saved {count} events for dt range {start} - {end}')
                amp_data_load()
                logger.info(f'Successfully loaded to S3')
            except Exception as e:
                logger.error(f'AMP events retry failed: {e}')


if __name__ == '__main__':
    amp_retry_function()   




