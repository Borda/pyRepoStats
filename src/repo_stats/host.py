"""
Copyright (C) 2020-2021 Jiri Borovec <...>
"""

import logging
import os
import re
from abc import abstractmethod
from typing import Dict, List, Optional, Tuple

import matplotlib.pyplot as plt
from tabulate import tabulate

from repo_stats.data_io import convert_date, is_in_time_period, load_data, save_data
from repo_stats.stats import compute_user_comment_timeline, compute_users_summary
from repo_stats.visual import draw_comments_timeline


class Host:
    """Template for any Git host."""

    #: host name, server
    HOST_NAME = "unknown"
    #: if host provides direct link to user
    USER_URL_TEMPLATE = "%(user)s"
    #: limit number of parallel requests to host
    NB_PARALLEL_REQUESTS = 7
    #: template name for exporting CSV with users overview
    CSV_USERS_SUMMARY = "%s_%s_users-summary.csv"
    #: template name for exporting CSV with comment's contributions
    CSV_USER_COMMENTS = "%s_%s_user-comments_freq:%s_type:%s.csv"
    #: template name for exporting Figure/PDF with comment's contributions
    PDF_USER_COMMENTS = "%s_%s_user-comments_freq:%s_type:%s.pdf"
    #: kay to the raw fetch data from host
    DATA_KEY_RAW_INFO = "raw_info"
    #: key to the raw fetch data from host
    DATA_KEY_RAW_TICKETS = "raw_tickets"
    #: simplified host data, collection of issues/PRs
    DATA_KEY_SIMPLE = "simple_tickets"
    #: timeline of all comments in the repo
    DATA_KEY_COMMENTS = "comments_timeline"
    #: define bot users as name pattern
    USER_BOTS = tuple()
    #: OS env. variable for getting Token
    OS_ENV_AUTH_TOKEN = "AUTH_API_TOKEN"
    #: common spam messages, no special value to give credit for it...
    SPAM_MESSAGES = (
        "done",
        "LGTM",
        "looks good to me",
        r"(Awesome|great|good|nice|well)\s+(work|job|done|neat)",
        "Thank you",
        "Thanks",
    )

    def __init__(
        self,
        repo_name: str,
        output_path: str,
        auth_token: Optional[str] = None,
        min_contribution: int = 3,
    ):
        """
        Args:
            repo_name: Repository name, need to  ne unique
            output_path: Path to saving dumped cache, csw tables, pdf figures
            auth_token: authentication token fro API access
            min_contribution: minimal nb contributions for visualization
        """
        self.repo_name = repo_name
        self.name = repo_name.replace("/", "-")
        self.output_path = os.path.realpath(os.path.expanduser(output_path))
        assert os.path.isdir(self.output_path), f"Wrong folder: {self.output_path}"
        self.min_contribution_count = min_contribution
        self.auth_token = auth_token
        os_token = os.getenv(self.OS_ENV_AUTH_TOKEN)
        if not self.auth_token and os_token:
            logging.debug(f"Using `{self.OS_ENV_AUTH_TOKEN}` from your OS environment variables...")
            self.auth_token = os_token

        self.data = {}
        self.outdated = 0
        self.timestamp = None
        self.datetime_from = None
        self.datetime_to = None

    @staticmethod
    def _is_spam_message(msg: str, thr: float = 0.2) -> bool:
        """Filter useless / spam messages, if the spa text takes most of the comment.

        >>> Host._is_spam_message("lgtm !")
        True
        >>> Host._is_spam_message("just fine...")
        False
        >>> Host._is_spam_message("Well   Done.")
        True
        """
        ratio = 0
        msg = " ".join(msg.split()).lower()
        for spam in Host.SPAM_MESSAGES:
            found = re.search(spam.lower(), msg)
            if found:
                ratio += len(found.group())
        if ratio:
            ratio /= float(len(msg))
        return ratio >= thr

    @abstractmethod
    def _convert_to_simple(self, collection: List[dict]) -> List[dict]:
        """Aggregate issue/PR affiliations."""

    @abstractmethod
    def _convert_comments_timeline(self, issues: List[dict]) -> List[dict]:
        """Aggregate comments for all issue/PR affiliations."""

    @abstractmethod
    def _fetch_info(self) -> List[dict]:
        """Download general package info."""

    @abstractmethod
    def _fetch_overview(self) -> List[dict]:
        """Download all info from repository screening."""

    def _is_user_bot(self, user: str) -> bool:
        """Allow filter bots from users."""
        return any(u in user for u in self.USER_BOTS)

    @abstractmethod
    def _update_details(self, collection: Dict[str, dict], collect_new: Dict[str, dict]) -> Dict[str, dict]:
        """Download all info if from screening."""

    def fetch_data(self, offline: bool = False) -> None:
        """Get all data - load and update if allowed."""
        logging.info("Fetch requested data...")
        self.data = load_data(path_dir=self.output_path, repo_name=self.repo_name, host=self.HOST_NAME)

        if not offline:
            self.data[self.DATA_KEY_RAW_INFO] = self._fetch_info()
            overview = self._fetch_overview()
            overview = {str(i["number"]): i for i in overview}

            self.data[self.DATA_KEY_RAW_TICKETS] = self._update_details(
                self.data.get(self.DATA_KEY_RAW_TICKETS, {}), overview
            )
            if self.outdated > 0:
                logging.warning(
                    "Updating from host was not completed, some of following steps may fail or being incorrect."
                )
            self.preprocess_data()

            save_data(self.data, path_dir=self.output_path, repo_name=self.repo_name, host=self.HOST_NAME)
        # take the saved date
        self.timestamp = self.data.get("updated_at")

    def preprocess_data(self) -> None:
        """Some pre-processing of raw data."""
        raw_tickets = self.data[self.DATA_KEY_RAW_TICKETS].values()
        self.data[self.DATA_KEY_SIMPLE] = self._convert_to_simple(raw_tickets)
        self.data[self.DATA_KEY_COMMENTS] = self._convert_comments_timeline(raw_tickets)

    def set_time_period(self, date_from: str = None, date_to: str = None) -> None:
        """Set optional time window for selections.

        Args:
            date_from: date/time for period start
            date_to: date/time for period ends
        """
        date_from = convert_date(date_from)
        if date_from:
            self.datetime_from = date_from
        date_to = convert_date(date_to)
        if date_to:
            self.datetime_to = date_to

    def _is_in_time_period(self, dt) -> bool:
        """Check if particular date is in in range"""
        return is_in_time_period(dt, datetime_from=self.datetime_from, datetime_to=self.datetime_to)

    def print_users_summary(self, columns: List[str]) -> str:
        """Show user contribution overview and print table to terminal with selected `columns`.

        Args:
            columns: select columns to be shown in terminal

        Returns:
            path to the exported table
        """
        logging.debug("Show users summary...")
        assert self.DATA_KEY_SIMPLE in self.data, "forgotten call `_convert_to_simple`"

        if not self.data.get(self.DATA_KEY_SIMPLE):
            logging.warning("No data to process/show.")
            return

        df_users = compute_users_summary(
            self.data[self.DATA_KEY_SIMPLE],
            datetime_from=self.datetime_from,
            datetime_to=self.datetime_to,
        )

        # filter columns which are possible
        avail_columns = df_users.columns
        miss_columns = [c for c in columns if c not in avail_columns]
        if miss_columns:
            logging.warning(
                f"You fave requested following columns {miss_columns} which are missing in the table,"
                f" these columns are available: {avail_columns}"
            )
        columns = [c for c in columns if c in avail_columns]

        if not columns:
            columns = list(df_users.columns)
            logging.warning(f"You have not set any column was recognised, so we show all: {columns}")

        # filter just some columns
        df_users = df_users[columns]
        df_users.sort_values(columns[0], ascending=False, inplace=True)
        csv_path = os.path.join(self.output_path, self.CSV_USERS_SUMMARY % (self.HOST_NAME, self.name))
        df_users.to_csv(csv_path)
        df_users.index = df_users.index.map(lambda u: self.USER_URL_TEMPLATE % {"user": u})
        print(
            tabulate(
                df_users[df_users[columns[0]] >= self.min_contribution_count],
                tablefmt="pipe",
                headers="keys",
            )
        )
        return csv_path

    def show_user_comments(self, freq: str = "W", parent_type: str = "", show_fig: bool = True) -> Tuple[str, str]:
        """Show aggregated user contribution statistics in a table and a double chart

        Args:
            freq: aggregation frequency - Day, Week, Month, ...
            parent_type: item kind like issue/PR
            show_fig: show figure after all

        Returns:
            path to CSV table and PDF figure
        """
        logging.info(f'Show comments aggregation for freq: "{freq}" & type: "{parent_type}"')
        assert self.DATA_KEY_COMMENTS in self.data, "forgotten call `convert_comments_timeline`"

        if not self.data.get(self.DATA_KEY_COMMENTS):
            logging.warning("No data to process/show.")
            return

        df_comments = compute_user_comment_timeline(
            self.data[self.DATA_KEY_COMMENTS],
            parent_type=parent_type,
            freq=freq,
        )
        csv_path = os.path.join(
            self.output_path, self.CSV_USER_COMMENTS % (self.HOST_NAME, self.name, freq, parent_type or "all")
        )
        df_comments.to_csv(csv_path)

        cum_sum = df_comments.sum(axis=0)
        select_users = list(cum_sum[cum_sum >= self.min_contribution_count].index)
        fig, extras = draw_comments_timeline(
            df_comments[select_users],
            title=f'User comments aggregation @{self.timestamp} - Freq: {freq}, Type:{parent_type or "all"}',
        )
        fig_path = os.path.join(
            self.output_path, self.PDF_USER_COMMENTS % (self.HOST_NAME, self.name, freq, parent_type or "all")
        )
        fig.savefig(fig_path, bbox_extra_artists=(extras["legend"], extras["colorbar"]), bbox_inches="tight")
        if not show_fig:
            plt.close(fig)

        return csv_path, fig_path
