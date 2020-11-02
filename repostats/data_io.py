"""
Copyright (C) 2020-2020 Jiri Borovec <...>
"""

import json
import os

import pandas as pd

from repostats import __version__

JSON_CACHE_NAME = 'dump-%s_%s.json'


def _make_json_name(repo_name: str, host: str = '') -> str:
    """Create standard file name."""
    return JSON_CACHE_NAME % (host, repo_name.replace('/', '-'))


def load_data(path_dir: str, repo_name: str, host: str = '') -> dict:
    """Load dumped data.

    :param path_dir: folder for saving data
    :param repo_name: repository name, it shall be uniques for given provider
    :param host: host or Git server provider
    :return: loaded processing data

    >>> data = {'item': 123}
    >>> pj = save_data(data, path_dir='.', repo_name='my/repo')
    >>> data2 = load_data(path_dir='.', repo_name='my/repo')
    >>> from pprint import pprint
    >>> pprint(data2)  # doctest: +ELLIPSIS
    {'item': 123, 'updated_at': '...', 'version': '...'}
    >>> os.remove(pj)
    """
    assert os.path.isdir(path_dir)
    cache_path = os.path.join(path_dir, _make_json_name(repo_name, host))

    if os.path.isfile(cache_path):
        with open(cache_path, 'r') as fp:
            data = json.load(fp)
    else:
        data = {'raw': {}}
    return data


def save_data(data: dict, path_dir: str, repo_name: str, host: str = '') -> str:
    """Dump processing data.

    :param data: saving processing data
    :param path_dir: folder for saving data
    :param repo_name: repository name, it shall be uniques for given provider
    :param host: host or Git server provider
    :return: path to the saved file
    """
    assert os.path.isdir(path_dir)
    cache_path = os.path.join(path_dir, _make_json_name(repo_name, host))

    data.update({
        'version': __version__,
        'updated_at': str(pd.datetime.today()),
    })

    with open(cache_path, 'w') as fp:
        json.dump(data, fp, ensure_ascii=False)

    return cache_path