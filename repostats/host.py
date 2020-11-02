"""
Copyright (C) 2020-2020 Jiri Borovec <...>
"""

import logging
import os
from abc import abstractmethod
from typing import Optional, Dict, List

from tabulate import tabulate

from repostats.data_io import load_data, save_data
from repostats.stats import compute_users_stat


class Host:
    """Template for any Git host."""

    #: host name, server
    HOST_NAME = 'unknown'
    #: if host provides direct link to user
    USER_URL_TEMPLATE = '%(user)s'
    #: define min number contributions
    MIN_CONTRIBUTION_COUNT = 3
    #: limit number of parallel requests to host
    NB_PARALLEL_REQUESTS = 7
    #: template name for exporting CSV
    CSV_USER_SUMMARY = '%s_%s_users-summary.csv'
    #:
    DATA_KEY_RAW = 'raw'
    #:
    DATA_KEY_SIMPLE = 'simple_items'

    def __init__(self, repo_name: str, output_path: str, auth_token: Optional[str] = None):
        self.repo_name = repo_name
        self.name = repo_name.replace('/', '-')
        self.output_path = output_path
        self.auth_token = auth_token
        self.data = {}
        self.outdated = 0

    @abstractmethod
    def _convert_to_simple(self, collection: List[dict]) -> List[dict]:
        """Aggregate issue/PR affiliations."""

    @abstractmethod
    def _fetch_overview(self) -> List[dict]:
        """Download all info if from screening."""

    @abstractmethod
    def _update_details(self, collection: Dict[str, dict], collect_new: Dict[str, dict]) -> Dict[str, dict]:
        """Download all info if from screening."""

    def fetch_data(self, offline: bool = False):
        """Get all data - load and update if allowed."""
        logging.info('Fetch requested data...')
        self.data = load_data(path_dir=self.output_path, repo_name=self.repo_name, host=self.HOST_NAME)

        if not offline:
            overview = self._fetch_overview()
            overview = {str(i['number']): i for i in overview}

            self.data[self.DATA_KEY_RAW] = self._update_details(self.data.get(self.DATA_KEY_RAW, {}), overview)
            if self.outdated > 0:
                logging.warning(
                    'Updating from host was not completed, some of following steps may fail or being incorrect.'
                )
            self.data[self.DATA_KEY_SIMPLE] = self._convert_to_simple(self.data[self.DATA_KEY_RAW].values())

            save_data(self.data, path_dir=self.output_path, repo_name=self.repo_name, host=self.HOST_NAME)

    def show_users_summary(self):
        assert self.DATA_KEY_SIMPLE in self.data, 'forgotten call `convert_to_items`'
        logging.debug(f'Show users stats for "{self.repo_name}"')
        df_users = compute_users_stat(self.data[self.DATA_KEY_SIMPLE])
        # filter just some columns
        df_users = df_users[['merged PRs', 'commented PRs', 'opened issues', 'commented issues', 'all opened']]
        df_users.to_csv(os.path.join(
            self.output_path,
            self.CSV_USER_SUMMARY % (self.HOST_NAME, self.name)))
        df_users.index = df_users.index.map(lambda u: self.USER_URL_TEMPLATE % {'user': u})
        print(tabulate(
            df_users[df_users['all opened'] >= self.MIN_CONTRIBUTION_COUNT],
            tablefmt="pipe",
            headers="keys",
        ))
