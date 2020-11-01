"""
Copyright (C) 2020-2020 Jiri Borovec <...>
"""

import json
import logging
import warnings
from functools import partial
from multiprocessing import Pool
from typing import Optional, Tuple

import pandas as pd
import requests
from tqdm import tqdm

from repostats.data_io import load_data, save_data

URL_GITHUB_API = 'https://api.github.com/repos'
JSON_CACHE_NAME = 'dump-github_%s.json'
NB_JOBS = 7
API_LIMIT_REACHED = False
API_LIMIT_MESSAGE = """
Request failed, probably you have reached free/personal request's limit...
To use higher limit generate personal auth token, see https://developer.github.com/v3/#rate-limiting
"""


def fetch_all_issues(gh_repo: str, auth_header: dict) -> list:
    """Fetch all issues from a given repo using listing per pages."""
    items, min_idx, page = [], float('inf'), 1
    # get items
    with tqdm(desc='Requesting issue/PR overview') as pbar:
        while min_idx > 1:
            req = requests.get(
                f"{URL_GITHUB_API}/{gh_repo}/issues"
                f"?state=all&page={page}&per_page=100",
                headers=auth_header,
            )
            if req.status_code == 403:
                exit(API_LIMIT_MESSAGE)
            items += json.loads(req.content)
            if page == 1:
                # in case there is no issue/pr
                if sum([isinstance(i, dict) for i in items]) == 0:
                    return []
                min_idx = items[0]['number']
                pbar.reset(total=min_idx)
            pbar.update(min_idx - items[-1]['number'])
            min_idx = items[-1]['number']
            page += 1
    return items


def _request_comments(comments_url: str, auth_header: dict) -> Optional[list]:
    """Request all comments from the issue life-time."""
    if API_LIMIT_REACHED:
        return None
    # https://api.github.com/repos/PyTorchLightning/pytorch-lightning/issues/37/comments
    req = requests.get(comments_url, headers=auth_header)
    if req.status_code == 403:
        return None
    comments = json.loads(req.content)
    return comments


def _request_detail_pr(url: str, auth_header: dict) -> Optional[str]:
    """Request PR status, in particular we want to distinguish between closed and merged ones."""
    url = url.replace('issues', 'pulls')
    if API_LIMIT_REACHED:
        return None
    req = requests.get(url, headers=auth_header)
    if req.status_code == 403:
        return None
    detail = json.loads(req.content)
    if 'merged_at' in detail:
        detail['state'] = 'merged'
    return detail


def update_detail(idx_item: Tuple[int, dict], auth_header: dict) -> tuple:
    """Get all needed issue/PR details"""
    idx, item = idx_item
    # this request is need only for PR, can be skipped for issues
    if 'pull' in item['html_url'].split('/'):
        detail = _request_detail_pr(item['url'], auth_header)
        if detail is None:
            return idx, None
        item.update(detail)
    extras = dict(
        # pull all comments
        comments=_request_comments(item['comments_url'], auth_header),
    )
    if any(dl is None for dl in extras.values()):
        return idx, None
    # update info
    item.update(extras)
    return idx, item


def update_details(issues: dict, issues_new: dict, auth_header: dict) -> dict:
    """Pull all exiting details to particular issues."""
    global API_LIMIT_REACHED
    # filter missing issue or issues which was updated since last time
    queue = [idx for idx in issues_new
             if (idx not in issues
                 or not issues[idx]['updated_at']
                 or pd.to_datetime(issues_new[idx]['updated_at']) > pd.to_datetime(issues[idx]['updated_at']))]
    if not queue:
        logging.info("All issues/PRs are up-to-date")
        return issues

    _queue = [(i, issues_new[i]) for i in queue]
    _update = partial(update_detail, auth_header=auth_header)
    pool = Pool(NB_JOBS)

    pbar = tqdm(total=len(queue), desc="Fetching/update details")
    for idx, item in pool.imap(_update, _queue):
        pbar.update()
        if item is None:
            if not API_LIMIT_REACHED:
                # show this warning only once
                warnings.warn(API_LIMIT_MESSAGE)
            API_LIMIT_REACHED = True
            # drop update date or another way to set that this issue was not fetch completely
            item = issues.get(idx, issues_new.get(idx))
            item['updated_at'] = None
        issues[idx] = item
    pbar.close()

    pool.close()
    pool.join()
    return issues


def convert_items(issues: list) -> list:
    """Aggregate issue/PR affiliations."""
    items = [dict(
        type='PR' if 'pull' in issue['html_url'] else 'issue',
        state=issue['state'],
        author=issue['user']['login'],
        commenters=[com['user']['login'] for com in issue['comments']
                    if '[bot]' not in com['user']['login']],
    ) for issue in issues]
    return items


def github_main(gh_repo: Optional[str], output_path: str, auth_token: Optional[str] = None, offline: bool = False):
    auth_header = {'Authorization': f'token {auth_token}'} if auth_token else {}

    data = load_data(path_dir=output_path, repo_name=gh_repo, host='github')

    if not offline:
        issues_new = fetch_all_issues(gh_repo, auth_header)
        issues_new = {str(i['number']): i for i in issues_new}

        data['raw'] = update_details(data['raw'], issues_new, auth_header)
        data['items'] = convert_items(data['raw'].values())

        save_data(data, path_dir=output_path, repo_name=gh_repo, host='github')

    if not data['items']:
        logging.warning('nothing to work on...')

    return data
