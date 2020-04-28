import pickle
from contextlib import contextmanager
from pathlib import Path

import numpy as np
import pandas as pd
import toml
from appdirs import AppDirs
from click import echo
from slugify import slugify

__all__ = [
    "MANIFEST_FNAME",
    "DATA_FNAME",
    "PROFILES_FNAME",
    "parse",
    "spec_profiles",
    "load",
    "manifest_keys",
    "open_data",
]

MANIFEST_FNAME = "manifest.pickle"
DATA_FNAME = "dataframe.pickle"
PROFILES_FNAME = "profiles.pickle"

TYPES_MAP = {"float": np.single, "int": np.intc}

dirs = AppDirs("prng")
data_dir = Path(dirs.user_data_dir)
manifest_path = data_dir / MANIFEST_FNAME

try:
    Path.mkdir(data_dir)
    echo(f"Created store folder at {data_dir}")
except FileExistsError:
    pass


class DataStoreExistsError(FileExistsError):
    pass


@contextmanager
def open_manifest(write=False):
    if not manifest_path.exists():
        manifest = {}
    else:
        with open(manifest_path, "rb") as f:
            try:
                manifest = pickle.load(f)
            except EOFError:
                manifest = {}

    if not write:
        yield manifest
    else:
        with open(manifest_path, "wb") as f:
            yield manifest
            pickle.dump(manifest, f)


def parse(datafile, specfile):
    spec = toml.load(specfile)

    df = pd.read_csv(datafile, header=None)

    dtype = TYPES_MAP[spec["dtype"]]
    df = df.astype(dtype)

    return df, spec


def spec_profiles(spec):
    defaults = {}
    profiles = []

    for key, value in spec.items():
        if type(value) is dict:
            profile = value
            profile["name"] = key
            profiles.append(profile)
        else:
            defaults[key] = value

    if len(profiles) == 0:
        profiles.append(defaults)
    else:
        for profile in profiles:
            for key, value in defaults.items():
                if key not in profile:
                    profile[key] = value

    return profiles


def load(datafile, specfile, overwrite=False):
    df, spec = parse(datafile, specfile)

    store_name = slugify(spec["name"])
    echo(f"Store name encoded as {store_name}")
    # TODO if name not specified, use timestamp

    store_path = data_dir / store_name
    try:
        Path.mkdir(store_path, exist_ok=overwrite)
        echo(f"Created store cache at {store_path}")
    except FileExistsError:
        raise DataStoreExistsError()

    data_path = store_path / DATA_FNAME
    pickle.dump(df, open(data_path, "wb"))

    profiles = spec_profiles(spec)
    profiles_path = store_path / PROFILES_FNAME
    pickle.dump(profiles, open(profiles_path, "wb"))

    with open_manifest(write=True) as manifest:

        manifest[store_name] = store_path


def manifest_keys():
    with open_manifest() as manifest:
        return manifest.keys()


class ManifestError(KeyError):
    pass


def store_path(store_name):
    with open_manifest() as manifest:
        try:
            path = manifest[store_name]
            return path
        except KeyError:
            raise ManifestError()


@contextmanager
def open_data(store_name):
    path = store_path(store_name)

    with open(path / DATA_FNAME, "rb") as f:
        data = pickle.load(f)

        yield data


@contextmanager
def open_profiles(store_name):
    path = store_path(store_name)

    with open(path / PROFILES_FNAME, "rb") as f:
        data = pickle.load(f)

        yield data


def rm_tree(path):
    """Credit to https://stackoverflow.com/a/58183834/5193926"""
    for child in path.glob("*"):
        if child.is_file():
            child.unlink()
        else:
            rm_tree(child)
    path.rmdir()


def drop(store_name):
    store_path = data_dir / store_name

    rm_tree(store_path)
