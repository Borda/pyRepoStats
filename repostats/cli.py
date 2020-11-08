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

PATH_ROOT = os.path.dirname(os.path.dirname(__file__))
#: define minimal user contribution to show in tables
MIN_CONTRIBUTION_COUNT = 3
#: OS env. variable for getting Token
ENV_VAR_AUTH_TOKEN = 'AUTH_TOKEN'
#: take global setting from OS env
SHOW_FIGURES = bool(int(os.getenv('SHOW_FIGURE', default=1)))


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
    # todo: consider use groups for options
    parser.add_argument('--users_summary', type=str, nargs='*',
                        help='Show the summary stats for each user, the fist one is used for sorting.')
    # todo: consider also what king of issue/PR here or another - tuple(type,freq)
    parser.add_argument('--user_comments', type=str, required=False, default=None, choices=['D', 'W', 'M', 'Y'],
                        help='Select granularity of timeline - Day, Week, Month.')

    args = parser.parse_args()
    logging.info('Parsed arguments: \n%s', pformat(vars(args)))
    return args


def init_host(args: Namespace) -> Host:
    if args.github_repo:
        host = GitHub(
            args.github_repo,
            output_path=args.output_path,
            auth_token=args.auth_token,
        )
    else:
        host = None
    return host


def main(args: Namespace):
    """Main entry point."""
    auth_token = os.getenv(ENV_VAR_AUTH_TOKEN)
    if not args.auth_token:
        logging.debug('Using `auth_token` from your OS environment variables...')
        args.auth_token = auth_token

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
        host.show_user_comments(freq=args.user_comments, show_fig=SHOW_FIGURES)

    # at the end show all figures
    if SHOW_FIGURES:
        plt.show()


def cli_main():
    logging.basicConfig(level=logging.INFO)
    logging.info('running...')
    main(get_arguments())
    logging.info('Done :]')


if __name__ == '__main__':
    cli_main()
