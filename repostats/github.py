"""
Copyright (C) 2020-2020 Jiri Borovec <...>
"""

import json
import logging
import warnings
from functools import partial
from multiprocessing import Pool
from typing import Optional, Tuple, Dict, List

import pandas as pd
import requests
from tqdm import tqdm

from repostats.host import Host


class GitHub(Host):

    #: host name, server
    HOST_NAME = 'github'
    #: if host provides direct link to user
    USER_URL_TEMPLATE = '[%(user)s](https://github.com/%(user)s)'
    #: name to the host
    URL_API = 'https://api.github.com/repos'
    #: if you have reached the number of free/allowed requests
    API_LIMIT_REACHED = False
    #: hint/explanation what happened
    API_LIMIT_MESSAGE = """
Request failed, probably you have reached free/personal request's limit...
To use higher limit generate personal auth token, see https://developer.github.com/v3/#rate-limiting
"""
    BOTS_USERS = ('pep8speaks', '[bot]')

    def __init__(self, repo_name: str, output_path: str, auth_token: Optional[str] = None):
        super().__init__(repo_name=repo_name, output_path=output_path, auth_token=auth_token)
        self.auth_header = {'Authorization': f'token {auth_token}'} if auth_token else {}

    def _fetch_overview(self) -> List[dict]:
        """Fetch all issues from a given repo using listing per pages."""
        items, min_idx, page = [], float('inf'), 1
        # get items
        with tqdm(desc='Requesting issue/PR overview') as pbar:
            while min_idx > 1:
                req_url = f"{self.URL_API}/{self.repo_name}/issues?state=all&page={page}&per_page=100"
                items_new = GitHub._request_url(req_url, self.auth_header)
                if items_new is None:
                    exit(self.API_LIMIT_MESSAGE)

                items += items_new
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

    @staticmethod
    def _request_url(url: str, auth_header: dict) -> Optional[dict]:
        """General request with checking if request limit was reached."""
        if GitHub.API_LIMIT_REACHED:
            return None
        req = requests.get(url, headers=auth_header)
        if req.status_code == 403:
            return None
        return json.loads(req.content.decode(req.encoding))

    @staticmethod
    def _request_comments(comments_url: str, auth_header: dict) -> Optional[list]:
        """Request all comments from the issue life-time."""
        # https://api.github.com/repos/PyTorchLightning/pytorch-lightning/issues/37/comments
        return GitHub._request_url(comments_url, auth_header)

    @staticmethod
    def _request_detail_pr(pr_url: str, auth_header: dict) -> Optional[dict]:
        """Request PR status, in particular we want to distinguish between closed and merged ones."""
        pr_url = pr_url.replace('issues', 'pulls')
        detail = GitHub._request_url(pr_url, auth_header)
        if detail and detail.get('merged_at'):
            detail['state'] = 'merged'
        return detail

    @staticmethod
    def _update_detail(idx_item: Tuple[int, dict], auth_header: dict) -> tuple:
        """Get all needed issue/PR details"""
        idx, item = idx_item
        # this request is need only for PR, can be skipped for issues
        if 'pull' in item['html_url'].split('/'):
            detail = GitHub._request_detail_pr(item['url'], auth_header)
            if detail is None:
                return idx, None
            item.update(detail)
        extras = dict(
            # pull all comments
            comments=GitHub._request_comments(item['comments_url'], auth_header),
        )
        if any(dl is None for dl in extras.values()):
            return idx, None
        # update info
        item.update(extras)
        return idx, item

    @staticmethod
    def __update_issues_queue(issues: Dict[str, dict], issues_new: Dict[str, dict]) -> List[str]:
        return [
            idx for idx in issues_new
            if (idx not in issues
                or not issues[idx]['updated_at']
                or pd.to_datetime(issues_new[idx]['updated_at']) > pd.to_datetime(issues[idx]['updated_at']))
        ]

    def _update_details(self, issues: Dict[str, dict], issues_new: Dict[str, dict]) -> Dict[str, dict]:
        """Pull all exiting details to particular issues."""
        # filter missing issue or issues which was updated since last time
        queue = self.__update_issues_queue(issues, issues_new)
        if not queue:
            logging.info("All issues/PRs are up-to-date")
            return issues

        _queue = [(i, issues_new[i]) for i in queue]
        _update = partial(GitHub._update_detail, auth_header=self.auth_header)
        pool = Pool(self.NB_PARALLEL_REQUESTS)

        for idx, item in tqdm(pool.imap(_update, _queue),
                              total=len(_queue),
                              desc="Fetching/update details"):
            if item is None:
                if not GitHub.API_LIMIT_REACHED:
                    # show this warning only once
                    warnings.warn(self.API_LIMIT_MESSAGE)
                GitHub.API_LIMIT_REACHED = True
                # drop update date or another way to set that this issue was not fetch completely
                item = issues.get(idx, issues_new.get(idx))
                item['updated_at'] = None
            issues[idx] = item

        pool.close()
        pool.join()
        self.outdated = len(self.__update_issues_queue(issues, issues_new))
        return issues

    @staticmethod
    def __parse_user(field: dict) -> str:
        return field['user']['login']

    def __is_user_bot(self, user: str) -> bool:
        return any(u in user for u in self.BOTS_USERS)

    def _convert_to_simple(self, issues: List[dict]) -> List[dict]:
        """Aggregate issue/PR affiliations."""
        items = [
            dict(
                type='PR' if 'pull' in issue['html_url'] else 'issue',
                state=issue['state'],
                author=self.__parse_user(issue),
                commenters=list(set(self.__parse_user(com) for com in issue['comments']
                                    if not self.__is_user_bot(self.__parse_user(com)))),
            )
            for issue in tqdm(issues, desc='Parsing simplified items')
            if isinstance(issue.get('comments'), list)
        ]
        return items

    def _convert_comments_timeline(self, issues: List[dict]) -> List[dict]:
        """Aggregate comments for all issue/PR affiliations."""
        comments = []
        for item in tqdm(issues, desc='Parsing comments from all repo'):
            item_comments = item.get('comments')
            if not isinstance(item_comments, list):
                continue
            comments += [
                dict(
                    parent_type='PR' if 'pull' in item['html_url'] else 'issue',
                    parent_idx=int(item['number']),
                    author=self.__parse_user(cmt),
                    created_at=cmt['created_at'],  # todo
                ) for cmt in item_comments if not self.__is_user_bot(self.__parse_user(cmt))
            ]
        return comments
