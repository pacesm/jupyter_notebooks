#
# Local model execution subroutines
#

import re
import time
import datetime
from os.path import join, exists, basename
from os import remove
from zipfile import ZipFile
from urllib.parse import urljoin
from urllib.request import urlopen
from shutil import copyfileobj
from numpy import datetime64, stack, zeros, asarray
from eoxmagmod.data import (
    CHAOS7_STATIC,
    IGRF13,
    LCS1,
    MF7,
)
from eoxmagmod import (
    load_model_shc,
    load_model_swarm_mio_internal,
    load_model_swarm_mio_external,
)
#from eoxmagmod.magnetic_model.parser_mma import _cdf_rawtime_to_mjd2000 as cdf_rawtime_to_mjd2000
from loader_mma import (
    load_model_swarm_mma_2c_internal,
    load_model_swarm_mma_2c_external,
)
from validation import get_data
from spacepy import pycdf

LOCAL_PATH = "./data"

EPOCH_2000 = datetime64("2000-01-01T00:00:00", "ns")
NS_TO_DATE = 1.0 / 86400000000000.0

CDF_EPOCH_TYPE = pycdf.const.CDF_EPOCH.value
CDF_EPOCH_2000 = 63113904000000.0


def cdf_rawtime_to_mjd2000(raw_time, cdf_type):
    """ Convert an array of CDF raw time values to array of MJD2000 values.
    """
    if cdf_type == CDF_EPOCH_TYPE:
        return (raw_time - CDF_EPOCH_2000) / 86400000.0
    raise TypeError("Unsupported CDF time type %r !" % cdf_type)


def datetime64_to_mjd2000(times):
    """ Convert Numpy.datetime64 array to MJD2000. """
    return (times.astype("datetime64[ns]") - EPOCH_2000).astype("int64") * NS_TO_DATE


def get_model_files(url, sources, pattern, extension, zip_extension=None, data_path=LOCAL_PATH):
    """ Download and unpack sources matched by the provided regex pattern.
    The function then returns a list of local files.
    """

    def get_file(name):
        """ Download file and unzip it is not present already. """
        target_file = join(data_path, name + extension)
        if not exists(target_file):
            downloaded_file = join(data_path, name + (zip_extension or extension))
            if not exists(downloaded_file):
                remote_url = urljoin(url, basename(downloaded_file))
                download_file(remote_url, downloaded_file)
            if downloaded_file != target_file:
                unzip_file(downloaded_file, target_file)
                if exists(target_file):
                    remove(downloaded_file)
        return target_file

    return [
        get_file(source) for source in sources
        if pattern.match(source)
    ]


def unzip_file(source, destination):
    """ Extract file from a Zip archive. """
    print(f"extracting {source} --> {destination} ... ", end="")
    with ZipFile(source) as zip_:
        for zipped_file in zip_.namelist():
            if basename(zipped_file) != basename(destination):
                continue
            with zip_.open(zipped_file) as file_in:
                with open(destination, "wb") as file_out:
                    copyfileobj(file_in, file_out)
        else:
            zip_.open(zipped_file) # throws an error
    print("OK")


def download_file(source, destination):
    """ Download file from a URL (supports both HTTP and FTP). """
    print(f"donwloading {source} --> {destination} ... ", end="")
    with urlopen(source) as response:
        with open(destination, "wb") as file:
            copyfileobj(response, file)
    print("OK")


def get_models(models, sources):
    """ Get list of models loaded from the given list of sources. """

    def get_model(model):
        return MODEL_LOADERS.get(model, lambda sources: [])(sources)

    return {
        model: get_model(model)
        for model in models
    }


MODEL_SOURCES = {
    "CHAOS-Static": lambda sources: [CHAOS7_STATIC],
    "CHAOS-Core": lambda sources: get_model_files(
        url="ftp://swarm-diss.eo.esa.int/Level2longterm/MCO/",
        sources=sources,
        pattern=re.compile("^SW_OPER_MCO_SHA_2X_"),
        extension=".shc",
        zip_extension=".ZIP"
    ),
    "CHAOS-MMA": lambda sources: ["./data/SW_OPER_MMA_CHAOS_.cdf"],
    # "CHAOS-MMA": lambda sources: get_model_files(
    #     url="https://www.spacecenter.dk/files/magnetic-models/RC/MMA/",
    #     sources=sources,
    #     pattern=re.compile("^SW_OPER_MMA_CHAOS__"),
    #     extension=".cdf",
    # ),
    "MIO_SHA_2C": lambda sources: get_model_files(
        url="ftp://swarm-diss.eo.esa.int/Level2longterm/MIO/",
        sources=sources,
        pattern=re.compile("^SW_OPER_MIO_SHA_2C_"),
        extension=".txt",
        zip_extension=".ZIP"
    ),
}


MODEL_LOADERS = {
    "CHAOS": lambda sources: [
        load_model_shc(*MODEL_SOURCES["CHAOS-Core"](sources)),
        load_model_shc(*MODEL_SOURCES["CHAOS-Static"](sources)),
        load_model_swarm_mma_2c_internal(*MODEL_SOURCES["CHAOS-MMA"](sources)),
        load_model_swarm_mma_2c_external(*MODEL_SOURCES["CHAOS-MMA"](sources)),
    ],
    "CHAOS-Static": lambda sources: [
        load_model_shc(*MODEL_SOURCES["CHAOS-Static"](sources)),
    ],
    "CHAOS-Core": lambda sources: [
        load_model_shc(*MODEL_SOURCES["CHAOS-Core"](sources)),
    ],
    "CHAOS-MMA": lambda sources: [
        load_model_swarm_mma_2c_internal(*MODEL_SOURCES["CHAOS-MMA"](sources)),
        load_model_swarm_mma_2c_external(*MODEL_SOURCES["CHAOS-MMA"](sources)),
    ],
    "CHAOS-MMA-Primary": lambda sources: [
        load_model_swarm_mma_2c_external(*MODEL_SOURCES["CHAOS-MMA"](sources)),
    ],
    "CHAOS-MMA-Secondary": lambda sources: [
        load_model_swarm_mma_2c_internal(*MODEL_SOURCES["CHAOS-MMA"](sources)),
    ],
    "MIO_SHA_2C": lambda sources: [
        load_model_swarm_mio_internal(*MODEL_SOURCES["MIO_SHA_2C"](sources)),
        load_model_swarm_mio_external(*MODEL_SOURCES["MIO_SHA_2C"](sources)),
    ],
    "MIO_SHA_2C-Primary": lambda sources: [
        load_model_swarm_mio_external(*MODEL_SOURCES["MIO_SHA_2C"](sources)),
    ],
    "MIO_SHA_2C-Secondary": lambda sources: [
        load_model_swarm_mio_internal(*MODEL_SOURCES["MIO_SHA_2C"](sources)),
    ],

}


def eval_models(name, models, data):
    print(f"evaluating model {name} ... ", end="")
    times = datetime64_to_mjd2000(data["Timestamp"].values)
    coords = stack([
        data["Latitude"].values,
        data["Longitude"].values,
        data["Radius"].values * 1e-3,
    ], axis=1)
    start = time.perf_counter_ns()
    result = zeros(coords.shape)
    # Note: The F10.7 index and sub-solar point parameters are required
    #       by the MIO models. Other models just ignore them.
    options = {
        "f107": data["F107"].values,
        "lat_sol": data["SunDeclination"].values,
        "lon_sol": data["SunLongitude"].values,
        "scale": asarray([1.0, 1.0, -1.0]),
    }
    for item in models:
        result += item.eval(times, coords, **options)
    stop = time.perf_counter_ns()
    duration = (stop - start) * 1e-9
    print(f"OK  {duration:g} s")
    return result


def eval_models_from_data_file(name, models, data_file):
    with pycdf.CDF(data_file) as cdf:
        times_var = cdf.raw_var("Timestamp")
        times = cdf_rawtime_to_mjd2000(times_var[...], times_var.type())
        coords = stack([
            cdf["Latitude"][...],
            cdf["Longitude"][...],
            cdf["Radius"][...] * 1e-3,
        ], axis=1)
        options = {
            "f107": cdf["F107"][...],
            "lat_sol": cdf["SunDeclination"][...],
            "lon_sol": cdf["SunLongitude"][...],
            "scale": asarray([1.0, 1.0, -1.0]),
        }
    print(f"evaluating model {name} ... ", end="")
    start = time.perf_counter_ns()
    result = zeros(coords.shape)
    # Note: The F10.7 index and sub-solar point parameters are required
    #       by the MIO models. Other models just ignore them.

    for item in models:
        result += item.eval(times, coords, **options)
    stop = time.perf_counter_ns()
    duration = (stop - start) * 1e-9
    print(f"OK  {duration:g} s")
    return result

def get_inputs_from_data(data):
    return {
        "times": datetime64_to_mjd2000(data["Timestamp"].values),
        "coords": stack([
            data["Latitude"].values,
            data["Longitude"].values,
            data["Radius"].values * 1e-3,
        ], axis=1),
    }

def get_inputs_from_data_file(data_file):
    with pycdf.CDF(data_file) as cdf:
        times_var = cdf.raw_var("Timestamp")
        return {
            "times": cdf_rawtime_to_mjd2000(times_var[...], times_var.type()),
            "coords": stack([
                cdf["Latitude"][...],
                cdf["Longitude"][...],
                cdf["Radius"][...] * 1e-3,
            ], axis=1)
        }


def get_compared_model_values(url, collection, start_time, end_time, models, **options):
    options = dict(
        collection=collection,
        start_time=start_time,
        end_time=end_time,
        models=models,
        auxiliaries=["F107", "SunLongitude", "SunDeclination"], # required by MIO modes
        **options,
    )

    for model in models:
        if "=" in model:
            raise ValueError("Local evaluation of model expressions is not yet supported.")

    data_file = "./data/data.cdf"
    data = get_data(url=url, data_file=data_file, **options)

    model_names = [
        model.partition("=")[0].strip() for model in models
    ]

    local_models = get_models(models, data.attrs['Sources'])

    return {
        "Timestamp": data["Timestamp"].values,
        "tested": {
            name: data[f"B_NEC_{name}"].values
            for name in model_names
        },
        "local": {
            **{
                name: eval_models(name, local_models[name], data)
                for name in model_names
            },
            "inputs": get_inputs_from_data(data),
        },
        "cdf": {
            **{
                name: eval_models_from_data_file(name, local_models[name], data_file)
                for name in model_names
            },
            "inputs": get_inputs_from_data_file(data_file),
        },

        "info": {
            "url": url,
            "collection": collection,
            "start": start_time.isoformat(),
            "end": end_time.isoformat(),
            "timestmap": datetime.datetime.utcnow().isoformat(),
            "model_names": model_names,
            "models": models,
        }
    }
