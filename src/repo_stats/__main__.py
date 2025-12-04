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


def main(
    github_repo: Optional[str] = None,
    auth_token: Optional[str] = None,
    offline: bool = False,
    output_path: str = PATH_ROOT,
    min_contribution: int = 3,
    users_summary: Optional[list[str]] = None,
    user_comments: Optional[list[str]] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
):
    """Parse Repository details.

    Args:
        github_repo: GitHub repository in format <owner>/<name>.
        auth_token: Personal Auth token needed for higher API request limit.
        offline: Skip updating all information from web.
        output_path: Path to output directory.
        min_contribution: Specify minimal user contribution for visualisations.
        users_summary: Show the summary stats for each user, the first one is used for sorting.
        user_comments: Select combination of granularity of timeline - [D]ay, [W]eek, [M]onth and [Y]ear,
            and item type - issue or PR. Valid values: D, W, M, Y, issue, pr, all.
        date_from: Define beginning time period.
        date_to: Define ending time period.

    """
    if not github_repo:
        exit("No repository specified.")

    default_params = {
        "output_path": output_path,
        "auth_token": auth_token,
        "min_contribution": min_contribution,
    }
    host = GitHub(github_repo, **default_params)

    host.fetch_data(offline)
    if not offline and host.outdated > 0:
        exit("The update failed to complete, pls try it again or run offline.")

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
                f"You have requested {user_comments} but not of them is time aggregation: {DATETIME_FREQ.keys()}"
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


def cli_main():
    """CLI entry point for backward compatibility."""
    logging.basicConfig(level=logging.INFO)
    logging.info("running...")
    from jsonargparse import ActionConfigFile, ArgumentParser

    parser = ArgumentParser(description="Parse Repository details")
    parser.add_argument("--config", action=ActionConfigFile)
    parser.add_argument(
        "-gh",
        "--github_repo",
        type=Optional[str],
        default=None,
        help="GitHub repository in format <owner>/<name>.",
    )
    parser.add_argument(
        "-t",
        "--auth_token",
        type=Optional[str],
        default=None,
        help="Personal Auth token needed for higher API request limit.",
    )
    parser.add_argument("--offline", action="store_true", help="Skip updating all information from web.")
    parser.add_argument(
        "-o",
        "--output_path",
        type=str,
        default=PATH_ROOT,
        help="Path to output directory.",
    )
    parser.add_argument(
        "-n",
        "--min_contribution",
        type=int,
        default=3,
        help="Specify minimal user contribution for visualisations.",
    )
    parser.add_argument(
        "--users_summary",
        default=None,
        nargs="*",
        help="Show the summary stats for each user, the first one is used for sorting.",
    )
    parser.add_argument(
        "--user_comments",
        default=None,
        nargs="*",
        help="Select combination of granularity of timeline - [D]ay, [W]eek, [M]onth and [Y]ear, "
        "and item type - issue or PR. Valid values: D, W, M, Y, issue, pr, all.",
    )
    parser.add_argument(
        "--date_from",
        type=Optional[str],
        default=None,
        help="Define beginning time period.",
    )
    parser.add_argument(
        "--date_to",
        type=Optional[str],
        default=None,
        help="Define ending time period.",
    )
    args = parser.parse_args()
    # Remove config argument before passing to main
    args_dict = vars(args)
    args_dict.pop("config", None)
    main(**args_dict)
    logging.info("Done :]")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    from jsonargparse import ActionConfigFile, ArgumentParser

    parser = ArgumentParser(description="Parse Repository details")
    parser.add_argument("--config", action=ActionConfigFile)
    parser.add_argument(
        "-gh",
        "--github_repo",
        type=Optional[str],
        default=None,
        help="GitHub repository in format <owner>/<name>.",
    )
    parser.add_argument(
        "-t",
        "--auth_token",
        type=Optional[str],
        default=None,
        help="Personal Auth token needed for higher API request limit.",
    )
    parser.add_argument("--offline", action="store_true", help="Skip updating all information from web.")
    parser.add_argument(
        "-o",
        "--output_path",
        type=str,
        default=PATH_ROOT,
        help="Path to output directory.",
    )
    parser.add_argument(
        "-n",
        "--min_contribution",
        type=int,
        default=3,
        help="Specify minimal user contribution for visualisations.",
    )
    parser.add_argument(
        "--users_summary",
        default=None,
        nargs="*",
        help="Show the summary stats for each user, the first one is used for sorting.",
    )
    parser.add_argument(
        "--user_comments",
        default=None,
        nargs="*",
        help="Select combination of granularity of timeline - [D]ay, [W]eek, [M]onth and [Y]ear, "
        "and item type - issue or PR. Valid values: D, W, M, Y, issue, pr, all.",
    )
    parser.add_argument(
        "--date_from",
        type=Optional[str],
        default=None,
        help="Define beginning time period.",
    )
    parser.add_argument(
        "--date_to",
        type=Optional[str],
        default=None,
        help="Define ending time period.",
    )
    args = parser.parse_args()
    # Remove config argument before passing to main
    args_dict = vars(args)
    args_dict.pop("config", None)
    main(**args_dict)
