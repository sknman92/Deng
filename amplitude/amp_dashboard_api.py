import os
import logging
from api_utils import _amp_api_call

# logging config
logging.basicConfig(
    filename=os.path.join(os.path.dirname(__file__), "amp.log"),
    filemode = "a",
    format = "%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    level=logging.INFO)

logger = logging.getLogger()

url = 'https://analytics.eu.amplitude.com/api/2/events/list'

try:
    _amp_api_call('https://analytics.eu.amplitude.com/api/2/events/list', 'dashboard_data')
except Exception as e:
    logger.error(f'Error pulling dashboard events: {e}')

