"""
Copyright (C) 2020-2020 Jiri Borovec <...>
"""

import logging
import os
from argparse import ArgumentParser, Namespace
from pprint import pformat

import matplotlib.pyplot as plt
from repostats.github import GitHub
from repostats.host import Host
from repostats.stats import DATETIME_FREQ

PATH_ROOT = os.path.dirname(os.path.dirname(__file__))
#: OS env. variable for getting Token
ENV_VAR_AUTH_TOKEN = 'AUTH_TOKEN'
#: take global setting from OS env
ENV_VAR_SHOW_FIGURES = 'SHOW_FIGURE'


def get_arguments():
    parser = ArgumentParser('Parse Repository details')
    parser.add_argument('-gh', '--github_repo', type=str, required=False, default=None,
                        help='GitHub repository in format <owner>/<name>.')
    parser.add_argument('-t', '--auth_token', type=str, required=False, default=None,
                        help='Personal Auth token needed for higher API request limit')
    parser.add_argument('--offline', action='store_true', help='Skip updating all information from web.')
    # todo: probably use some other temp folder
    parser.add_argument('-o', '--output_path', type=str, required=False, default=PATH_ROOT,
                        help='Personal Auth token needed for higher API request limit.')
    parser.add_argument('-n', '--min_contribution', type=int, required=False, default=3,
                        help='Specify minimal user contribution for visualisations.')
    # todo: consider use groups for options
    parser.add_argument('--users_summary', type=str, nargs='*',
                        help='Show the summary stats for each user, the fist one is used for sorting.')
    parser.add_argument('--user_comments', type=str, required=False, default=None, nargs='*',
                        choices=['D', 'W', 'M', 'Y', 'issue', 'pr', 'all'],
                        help='Select combination of granularity of timeline - [D]ay, [W]eek, [M]onth and [Y]ear,'
                             ' and item type - issue or PR (if you not specify, all will be used).')

    args = parser.parse_args()
    logging.info('Parsed arguments: \n%s', pformat(vars(args)))
    return args


def init_host(args: Namespace) -> Host:
    default_params = dict(
        output_path=args.output_path,
        auth_token=args.auth_token,
        min_contribution=args.min_contribution,
    )
    if args.github_repo:
        host = GitHub(args.github_repo, **default_params)
    else:
        host = None
    return host


def main(args: Namespace):
    """Main entry point."""
    auth_token = os.getenv(ENV_VAR_AUTH_TOKEN)
    if not args.auth_token:
        logging.debug('Using `auth_token` from your OS environment variables...')
        args.auth_token = auth_token
    show_figures = bool(int(os.getenv(ENV_VAR_SHOW_FIGURES, default=1)))

    host = init_host(args)
    if not host:
        exit('No repository specified.')

    host.fetch_data(args.offline)
    if not args.offline and host.outdated > 0:
        exit('The update failed to complete, pls try it again or run offline.')

    logging.info('Process requested stats...')
    if args.users_summary:
        host.show_users_summary(columns=args.users_summary)

    if args.user_comments:
        freqs = [f for f in args.user_comments if f in DATETIME_FREQ]
        types = [t for t in args.user_comments if t not in DATETIME_FREQ]
        if not freqs:
            logging.warning(
                f'You have requested {args.user_comments} but not of them is time aggregation: {DATETIME_FREQ.keys()}'
            )
        # if none set, use all
        types = ['all'] if not types else types
        for freq in freqs:
            for tp in types:
                tp = '' if tp.lower() == 'all' else tp
                host.show_user_comments(freq=freq, parent_type=tp, show_fig=show_figures)

    # at the end show all figures
    if show_figures:
        plt.show()


def cli_main():
    logging.basicConfig(level=logging.INFO)
    logging.info('running...')
    main(get_arguments())
    logging.info('Done :]')


if __name__ == '__main__':
    cli_main()
