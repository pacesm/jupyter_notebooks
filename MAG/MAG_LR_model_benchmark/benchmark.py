#
# common benchmark subroutines
#
#
#
#

import requests
import random
import time
import json
import datetime
import zoneinfo
from viresclient import SwarmRequest
from viresclient._wps.time_util import parse_datetime, parse_duration

TZ_UTC = zoneinfo.ZoneInfo("UTC")


def get_random_collection(collections):
    return random.choice(collections)


def get_random_time(start, end):
    total_seconds = max(0, int((end - start).total_seconds()))
    random_seconds = random.randrange(total_seconds)
    return start + datetime.timedelta(seconds=random_seconds)


def get_collection_date_range(url, collection):
    """ Get collection start and stop dates. """
    info = requests.get(f"{url}/hapi/info?dataset={collection}").json()
    return (
        parse_datetime(info["startDate"]),
        parse_datetime(info["stopDate"]),
    )


def measure_request_duration(url, collection, start_time, end_time, auxiliaries=None, models=None, filters=None):
    request = SwarmRequest(f"{url}/ows")
    request.set_collection(collection)
    request.set_products(
        measurements=["B_NEC"],
        auxiliaries=auxiliaries,
        models=models,
    )
    for filter_ in filters or ():
        request.add_filter(filter_)
    request_start = time.perf_counter_ns()
    data = request.get_between(
        start_time=start_time,
        end_time=end_time,
        asynchronous=False,
        show_progress=False,
    )
    request_stop = time.perf_counter_ns()
    request_duration = (request_stop - request_start) * 1e-9
    xdata = data.as_xarray() 
    size = xdata["Timestamp"].shape[0]
    return request_duration, size


MODELS = [
    "CHAOS-Core",
    "CHAOS-Static",
    "CHAOS-MMA-Primary",
    "CHAOS-MMA-Secondary",
    "CHAOS-MMA",
    "CHAOS",
    "MIO_SHA_2C-Primary",
    "MIO_SHA_2C-Secondary",
    "MIO_SHA_2C",
]


def run_benchmark(url, description, collection, start_time, end_time, **options):
    elapsed_time, size = measure_request_duration(
        url=url,
        collection=collection,
        start_time=start_time,
        end_time=end_time,
        **options
    )
    print(f"{size} {elapsed_time:.3g}s {description}")
    return {
        "timestamp": datetime.datetime.now(TZ_UTC),
        "serverURL": url,
        "collection": collection,
        "startTime": start_time,
        "endTime": end_time,
        "requestDuration": elapsed_time,
        "numberOfSamples": size,
        "description": description,
    }


def run_benchmark_set(url, collection, selection_time, test_cases):
    selection_time = parse_duration(selection_time)
    collection_start_time, collection_end_time = get_collection_date_range(url, collection)
    start_time = get_random_time(
        collection_start_time,
        collection_end_time - selection_time
    )
    end_time = start_time + selection_time
    common_options = {
        "url": url,
        "collection": collection,
        "start_time": start_time,
        "end_time": end_time,
    }
    for options in test_cases:
        yield run_benchmark(**common_options, **options)


def write_record(record, file):
    print(json.dumps(record, default=json_serialize), file=file)
    file.flush()


def json_serialize(obj):
    """Serialize data not serialized by default JSON serializer. """
    if isinstance(obj, (datetime.datetime, datetime.date)):
        return obj.isoformat()
    if isinstance(obj, datetime.timedelta):
        return obj.total_seconds()
    raise TypeError(f"Cannot serialize {type(obj)}!")