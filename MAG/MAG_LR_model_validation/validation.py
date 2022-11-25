#
# common validation subroutines
#

import numpy
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


def get_data(url, collection, start_time, end_time, auxiliaries=None, models=None, filters=None, data_file=None):
    request = SwarmRequest(f"{url}/ows")
    request.set_collection(collection)
    request.set_products(
        measurements=["B_NEC"],
        auxiliaries=auxiliaries,
        models=models,
        sampling_step="PT60S"
    )
    for filter_ in filters or ():
        request.add_filter(filter_)
    request_start = time.perf_counter_ns()
    data = request.get_between(
        start_time=start_time,
        end_time=end_time,
        #asynchronous=False,
        #show_progress=False,
    )
    request_stop = time.perf_counter_ns()
    request_duration = (request_stop - request_start) * 1e-9
    print(f"{url} {request_duration:g}s")
    if data_file:
        data.to_file(data_file, overwrite=True)
    return data.as_xarray()


def get_compared_model_values(tested_url, reference_url, collection, start_time, end_time, models, **options):
    options = dict(
        collection=collection,
        start_time=start_time,
        end_time=end_time,
        models=models,
        **options,
    )

    reference_data = get_data(url=reference_url, **options)
    tested_data = get_data(url=tested_url, **options)

    for key in ["Timestamp", "Radius", "Latitude", "Longitude"]:
        if not numpy.array_equal(tested_data[key].values, reference_data[key].values):
            raise ValueError(f"{key} mismatch! ({collection}, {start_time.isoformat()}/{end_time.isoformat()})")

    model_names = [
        model.partition("=")[0].strip() for model in models
    ]

    return {
        "Timestamp": reference_data["Timestamp"].values,
        "tested": {
            name: tested_data[f"B_NEC_{name}"].values
            for name in model_names
        },
        "reference": {
            name: reference_data[f"B_NEC_{name}"].values
            for name in model_names
        },
        "info": {
            "tested_url": tested_url,
            "reference_url": reference_url,
            "collection": collection,
            "start": start_time.isoformat(),
            "end": end_time.isoformat(),
            "timestmap": datetime.datetime.utcnow().isoformat(),
            "model_names": model_names,
            "models": models,
        }
    }
