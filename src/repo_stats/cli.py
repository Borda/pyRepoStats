"""
Copyright (C) 2020-2021 Jiri Borovec <...>
"""

import logging
import os
from typing import Optional

import matplotlib.pyplot as plt

from repo_stats.github import GitHub
from repo_stats.stats import DATETIME_FREQ

PATH_ROOT = os.path.dirname(os.path.dirname(__file__))
#: take global setting from OS env
SHOW_FIGURES = bool(int(os.getenv("SHOW_FIGURE", default=1)))


def scrape(
    github_repo: str,
    auth_token: Optional[str] = None,
    output_path: str = PATH_ROOT,
):
    """Scrape repository data from GitHub.

    Args:
        github_repo: GitHub repository in format <owner>/<name>.
        auth_token: Personal Auth token needed for higher API request limit.
        output_path: Path to output directory.

    """
    host = GitHub(
        repo_name=github_repo,
        output_path=output_path,
        auth_token=auth_token,
        min_contribution=1,  # Default value, not relevant for scraping
    )

    host.fetch_data(offline=False)
    if host.outdated > 0:
        exit("The update failed to complete, please try again.")

    logging.info("Data scraped successfully.")


def analyze(
    github_repo: str,
    auth_token: Optional[str] = None,
    output_path: str = PATH_ROOT,
    min_contribution: int = 3,
    offline: bool = True,
    users_summary: Optional[list[str]] = None,
    user_comments: Optional[list[str]] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
):
    """Analyze repository data.

    Args:
        github_repo: GitHub repository in format <owner>/<name>.
        auth_token: Personal Auth token needed for higher API request limit.
        output_path: Path to output directory.
        min_contribution: Specify minimal user contribution for visualisations.
        offline: Skip updating data from web (default: True, uses cached data).
        users_summary: Show the summary stats for each user, the first one is used for sorting.
        user_comments: Select combination of granularity of timeline - [D]ay, [W]eek, [M]onth and [Y]ear,
            and item type - issue or PR. Valid values: D, W, M, Y, issue, pr, all.
        date_from: Define beginning time period.
        date_to: Define ending time period.

    """
    host = GitHub(
        repo_name=github_repo,
        output_path=output_path,
        auth_token=auth_token,
        min_contribution=min_contribution,
    )

    # Load data (offline by default, can fetch fresh data if offline=False)
    host.fetch_data(offline=offline)
    if not offline and host.outdated > 0:
        exit("The update failed to complete, please try it again or run offline.")

    host.set_time_period(date_from=date_from, date_to=date_to)
    host.preprocess_data()

    logging.info("Process requested stats...")
    if users_summary:
        host.print_users_summary(columns=users_summary)

    if user_comments:
        freqs = [f for f in user_comments if f in DATETIME_FREQ]
        types = [t for t in user_comments if t not in DATETIME_FREQ]
        if not freqs:
            logging.warning(
                f"You have requested {user_comments} but none of them is time aggregation: {DATETIME_FREQ.keys()}"
            )
        # if none set, use all
        types = types or ["all"]
        for freq in freqs:
            for tp in types:
                tp = "" if tp.lower() == "all" else tp
                host.show_user_comments(freq=freq, parent_type=tp, show_fig=SHOW_FIGURES)

    # at the end show all figures
    if SHOW_FIGURES:
        plt.show()
