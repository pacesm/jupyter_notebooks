#
# subroutines used for HAPI testing
#

import time
import datetime
import random
import requests
from viresclient._wps.time_util import parse_datetime, parse_duration


def test_hapi(url):

    capabilities = get_capabilities(url)
    formats = capabilities["outputFormats"]
    
    catalog = get_catalog(url)   
    datasets = [item["id"] for item in catalog["catalog"]]

    for dataset in datasets:
        test_dataset(url, dataset, formats)

          
def test_dataset(url, dataset, formats):
    print(dataset, end=" ")

    info = get_info(url, dataset)
    dataset_start = parse_datetime(info["startDate"])
    dataset_end = parse_datetime(info["stopDate"])
    time_selection = parse_duration(info["x_maxTimeSelection"]) / 10

    print(f"{dataset_start.isoformat()}/{dataset_end.isoformat()}")

    if dataset_end - dataset_start < time_selection:
        time_selection = dataset_end - dataset_start
    
    start_time = get_random_time(dataset_start, dataset_end - time_selection)
    end_time = start_time + time_selection
    
    for format_ in formats:
        try:
            test_dataset_request(url, dataset, format_, start_time, end_time)
            request_stop = time.perf_counter_ns()
        except Exception as error:
            print(f"ERROR: {error}")


def test_dataset_request(url, dataset, format, start_time, end_time):
    print(f" - {dataset} {format} {start_time.isoformat()}/{end_time.isoformat()} ...", end=" ")
    request_start = time.perf_counter_ns()
    response = get_data(url, dataset, start_time, end_time, format)
    request_end = time.perf_counter_ns()
    if response.status_code != 200:
        print("ERROR:", f"{response.status_code} {response.json()}")
        return
    request_duration = (request_end - request_start) * 1e-9
    response_size = len(response.content)
    print(f"{response_size/(1024*1024):.1f}MB {request_duration:.3g}s")

    
def get_capabilities(url):
    """ Get HAPI server capabilities. """
    return requests.get(f"{url}/hapi/capabilities").json()

    
def get_catalog(url):
    """ List datasets offered by the server. """
    return requests.get(f"{url}/hapi/catalog").json()
    

def get_info(url, dataset):
    """ Get dataset description. """
    return requests.get(f"{url}/hapi/capabilities").json()


def get_info(url, dataset):
    """ Get dataset description. """
    return requests.get(f"{url}/hapi/info?dataset={dataset}").json()


def get_data(url, dataset, start_time, end_time, format):
    """ Get data response. """
    #https://staging.viresdisc.vires.services/hapi/data?dataset=SW_OPER_MAGA_LR_1B&parameters=Latitude,Longitude,Radius,B_NEC,Flags_B&start=2013-11-25T11:02:52Z&stop=2013-11-25T11:03:02Z&format=json&include=header
    return requests.get(
        f"{url}/hapi/data"
        f"?dataset={dataset}"
        f"&start={start_time.isoformat()}"
        f"&stop={end_time.isoformat()}"
        f"&format={format}"
        "&include=header"
    )


def get_random_time(start, end):
    total_seconds = max(0, int((end - start).total_seconds()))
    random_seconds = random.randrange(total_seconds) if total_seconds > 0 else 0.0
    return start + datetime.timedelta(seconds=random_seconds)