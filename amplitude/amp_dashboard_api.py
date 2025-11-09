import logging
from api_utils import _api_call, _saving_api_response

# logging config
logging.basicConfig(
    filename="amp.log",
    filemode = "a",
    format = "%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    level=logging.INFO)

logger = logging.getLogger()

url = 'https://analytics.eu.amplitude.com/api/2/events/list'

try:
    response, extract_time = _api_call('https://analytics.eu.amplitude.com/api/2/events/list')
    _saving_api_response(response, 'list_data', extract_time)
    logger.info(f'Successfully saved list data: extracted {extract_time}')
except Exception as e:
    logger.error(f'Error pulling list data: {e}')

