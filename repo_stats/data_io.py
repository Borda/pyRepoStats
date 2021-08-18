"""
Copyright (C) 2020-2021 Jiri Borovec <...>
"""
import codecs
import json
import logging
import os
from datetime import datetime
from distutils.version import LooseVersion
from typing import Any, Union
from warnings import warn

import pandas as pd
from pandas.errors import ParserError

from repo_stats import __version__

JSON_CACHE_NAME = 'dump-%s_%s.json'


def _make_json_name(repo_name: str, host: str = '') -> str:
    """Create standard file name."""
    return JSON_CACHE_NAME % (host, repo_name.replace('/', '-'))


def load_data(path_dir: str, repo_name: str, host: str = '') -> dict:
    """Load dumped data.

    Args:
        path_dir: folder for saving data
        repo_name: repository name, it shall be uniques for given provider
        host: host or Git server provider

    Returns:
        loaded processing data

    Example:
        >>> data = {'item': 123}
        >>> pj = save_data(data, path_dir='.', repo_name='my/repo')
        >>> data2 = load_data(path_dir='.', repo_name='my/repo')
        >>> from pprint import pprint
        >>> pprint(data2)  # doctest: +ELLIPSIS
        {'host-name': '',
         'item': 123,
         'repo-name': 'my/repo',
         'updated_at': '...',
         'version': '...'}
        >>> os.remove(pj)
    """
    assert os.path.isdir(path_dir), f'Wrong folder: {path_dir}'
    cache_path = os.path.join(path_dir, _make_json_name(repo_name, host))
    logging.info(f'Loading data from: {cache_path}')

    if os.path.isfile(cache_path):
        with codecs.open(cache_path, 'r', encoding='utf8') as fp:
            data = json.load(fp)
        data['version'] = data.get('version', '0.0')

        if LooseVersion(data['version']) < LooseVersion("0.1.4"):
            warn(
                f"Your last dump was made with {data['version']} which has missing review comments.\n"
                " We highly recommend to invalidate this cache and fetch all data from the ground..."
            )
    else:
        data = {}
    return data


def save_data(data: dict, path_dir: str, repo_name: str, host: str = '') -> str:
    """Dump processing data.

    Args:
        data: saving processing data
        path_dir: folder for saving data
        repo_name: repository name, it shall be uniques for given provider
        host: host or Git server provider

    Returns:
        path to the saved file
    """
    assert os.path.isdir(path_dir)
    cache_path = os.path.join(path_dir, _make_json_name(repo_name, host))
    logging.info(f'Saving data to: {cache_path}')

    data.update({
        'version': __version__,
        'updated_at': str(datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")),
        'host-name': host,
        'repo-name': repo_name,
    })

    # todo: consider saving to another/tep file and replace afterwords, prevent interruption while dump
    with codecs.open(cache_path, 'w', encoding='utf8') as fp:
        json.dump(data, fp, ensure_ascii=False)

    return cache_path


def convert_date(date: Any):
    """Convert date-time if possible

    >>> convert_date("2020-08")
    Timestamp('2020-08-01 00:00:00+0000', tz='UTC')
    """
    if not date:
        return date
    try:
        date = pd.to_datetime(date)
    except ParserError:
        warn(f"Unrecognised/invalid date format for input: {date}")
        date = None
    # need to set TimeZone cor comparison
    if date and not date.tzname():
        date = date.tz_localize(tz='UTC')
    return date


def is_in_time_period(
    dt: Union[datetime, str],
    datetime_from: Union[datetime, str] = None,
    datetime_to: Union[datetime, str] = None,
) -> bool:
    """ Check if particular date is in range.

    >>> is_in_time_period('2020', datetime_from=pd.to_datetime('2019'))
    True
    >>> is_in_time_period('2020-08-02', datetime_to='2020-09')
    True
    """
    # convert to comparable format
    dt, datetime_from, datetime_to = convert_date(dt), convert_date(datetime_from), convert_date(datetime_to)
    # initial setting - in case no range given all is fine
    is_in = True

    if not datetime_from and not datetime_to:
        is_in = True
    # in case there is no date spec, it is automatically false
    if not dt and (datetime_from or datetime_to):
        is_in = False
    else:
        # step-by-step checking
        if datetime_from:
            is_in &= dt >= datetime_from
        if datetime_to:
            is_in &= dt <= datetime_to
    return is_in
