import logging
from api_utils import _api_call, _saving_api_response
from load_utils import amp_data_load, retry

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

url = 'https://analytics.eu.amplitude.com/api/2/events/list'

@retry(retries = 3, sleep = 5)
def dashboard_api_call():
    try:
        response, extract_time = _api_call(url)
        _saving_api_response(response, 'list_data', extract_time)
        print(f'Successfully saved list data: extracted {extract_time}')
        logger.info(f'Successfully saved list data: extracted {extract_time}')
    except Exception as e:
        logger.error(f'Error pulling list data: {e}')

    try: 
        # uploading to s3
        amp_data_load()
        logger.info(f'Successfully loaded events list data to S3')
    except Exception as e:
        logger.error(f'Failed to load events list data: {e}')

if __name__ == '__main__':
    dashboard_api_call()




