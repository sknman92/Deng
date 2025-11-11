from bike_api import api_call_with_retries
from bike_point_load import bike_load

# for reloading libs
import importlib
import bike_api
import bike_point_load
importlib.reload(bike_api)
importlib.reload(bike_point_load)

if __name__ == '__main__':
    api_call_with_retries()
    bike_load()