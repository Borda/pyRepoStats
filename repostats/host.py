"""
Copyright (C) 2020-2020 Jiri Borovec <...>
"""

import logging
import os
from abc import abstractmethod
from typing import Optional, Dict, List

import matplotlib.pyplot as plt
from tabulate import tabulate

from repostats.data_io import load_data, save_data
from repostats.stats import compute_users_summary, compute_user_comment_timeline
from repostats.visual import draw_comments_timeline


class Host:
    """Template for any Git host."""

    #: host name, server
    HOST_NAME = 'unknown'
    #: if host provides direct link to user
    USER_URL_TEMPLATE = '%(user)s'
    #: limit number of parallel requests to host
    NB_PARALLEL_REQUESTS = 7
    #: template name for exporting CSV with users overview
    CSV_USERS_SUMMARY = '%s_%s_users-summary.csv'
    #: template name for exporting CSV with comment's contributions
    CSV_USER_COMMENTS = '%s_%s_user-comments_freq:%s_type:%s.csv'
    #: template name for exporting Figure/PDF with comment's contributions
    PDF_USER_COMMENTS = '%s_%s_user-comments_freq:%s_type:%s.pdf'
    #: kay to the raw fetch data from host
    DATA_KEY_RAW = 'raw'
    #: simplified host data, collection of issues/PRs
    DATA_KEY_SIMPLE = 'simple_items'
    #: timeline of all comments in the repo
    DATA_KEY_COMMENTS = 'comments_timeline'
    #: define bot users as name pattern
    USER_BOTS = tuple()

    def __init__(
            self,
            repo_name: str,
            output_path: str,
            auth_token: Optional[str] = None,
            min_contribution: int = 3,
    ):
        """
        :param repo_name: Repository name, need to  ne unique
        :param output_path: Path to saving dumped cache, csw tables, pdf figures
        :param auth_token: authentication token fro API access
        :param min_contribution: minimal nb contributions for visualization
        """
        self.repo_name = repo_name
        self.name = repo_name.replace('/', '-')
        self.output_path = output_path
        self.auth_token = auth_token
        self.min_contribution_count = min_contribution
        self.data = {}
        self.outdated = 0

    @abstractmethod
    def _convert_to_simple(self, collection: List[dict]) -> List[dict]:
        """Aggregate issue/PR affiliations."""

    @abstractmethod
    def _convert_comments_timeline(self, issues: List[dict]) -> List[dict]:
        """Aggregate comments for all issue/PR affiliations."""

    @abstractmethod
    def _fetch_overview(self) -> List[dict]:
        """Download all info if from screening."""

    def _is_user_bot(self, user: str) -> bool:
        """Allow filter bots from users."""
        return any(u in user for u in self.USER_BOTS)

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
            self.data[self.DATA_KEY_COMMENTS] = self._convert_comments_timeline(self.data[self.DATA_KEY_RAW].values())

            save_data(self.data, path_dir=self.output_path, repo_name=self.repo_name, host=self.HOST_NAME)

    def show_users_summary(self, columns: List[str]):
        """Show user contribution overview and print table to terminal with selected `columns`.

        :param columns: select columns to be shown in terminal
        :return: path to the exported table
        """
        assert self.DATA_KEY_SIMPLE in self.data, 'forgotten call `convert_to_items`'

        if not self.data.get(self.DATA_KEY_SIMPLE):
            logging.warning('No data to process/show.')
            return

        logging.debug(f'Show users stats for "{self.repo_name}"')
        df_users = compute_users_summary(self.data[self.DATA_KEY_SIMPLE])

        # filter columns which are possible
        aval_columns = df_users.columns
        miss_columns = [c for c in columns if c not in aval_columns]
        if miss_columns:
            logging.warning(f'You fave requested following columns {miss_columns} which are missing in the table,'
                            f' these columns are available: {aval_columns}')
        columns = [c for c in columns if c in aval_columns]

        if not columns:
            columns = list(df_users.columns)
            logging.warning(f'You have not set any column was recognised, so we show all: {columns}')

        # filter just some columns
        df_users = df_users[columns]
        df_users.sort_values(columns[0], ascending=False, inplace=True)
        csv_path = os.path.join(self.output_path, self.CSV_USERS_SUMMARY % (self.HOST_NAME, self.name))
        df_users.to_csv(csv_path)
        df_users.index = df_users.index.map(lambda u: self.USER_URL_TEMPLATE % {'user': u})
        print(tabulate(
            df_users[df_users[columns[0]] >= self.min_contribution_count],
            tablefmt="pipe",
            headers="keys",
        ))
        return csv_path

    def show_user_comments(self, freq: str = 'W', parent_type: str = '', show_fig: bool = True):
        """Show aggregated user contribution statistics in a table and a double chart

        :param freq: aggregation frequency - Day, Week, Month, ...
        :param parent_type: item kind like issue/PR
        :param show_fig: show figure after all
        :return: path to CSV table and PDF figure
        """
        assert self.DATA_KEY_COMMENTS in self.data, 'forgotten call `convert_comments_timeline`'

        if not self.data.get(self.DATA_KEY_COMMENTS):
            logging.warning('No data to process/show.')
            return

        logging.debug(f'Show comments stats for "{self.repo_name}"')
        df_comments = compute_user_comment_timeline(
            self.data[self.DATA_KEY_COMMENTS],
            parent_type=parent_type,
            freq=freq,
        )
        csv_path = os.path.join(self.output_path,
                                self.CSV_USER_COMMENTS % (self.HOST_NAME, self.name, freq, parent_type))
        df_comments.to_csv(csv_path)

        cum_sum = df_comments.sum(axis=0)
        select_users = list(cum_sum[cum_sum >= self.min_contribution_count].index)
        fig = draw_comments_timeline(
            df_comments[select_users], title=f'User comments aggregation - Freq: {freq}, Type:{parent_type}'
        )
        fig_path = os.path.join(self.output_path,
                                self.PDF_USER_COMMENTS % (self.HOST_NAME, self.name, freq, parent_type))
        fig.savefig(fig_path)
        if not show_fig:
            plt.close(fig)

        return csv_path, fig_path
