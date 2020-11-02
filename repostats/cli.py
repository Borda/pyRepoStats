"""
Copyright (C) 2020-2020 Jiri Borovec <...>
"""

import logging
import os
from argparse import ArgumentParser, Namespace
from pprint import pformat

from repostats.github import GitHub
from repostats.host import Host

PATH_ROOT = os.path.dirname(os.path.dirname(__file__))
MIN_CONTRIBUTION_COUNT = 3


def get_arguments():
    parser = ArgumentParser('Parse Repository details')
    parser.add_argument('-gh', '--github_repo', type=str, required=False, default=None,
                        help='GitHub repository in format <owner>/<name>.')
    parser.add_argument('-t', '--auth_token', type=str, required=False, default=None,
                        help='Personal Auth token needed for higher API request limit')
    parser.add_argument('--offline', action='store_true', help='Skip updating all information from web.')
    parser.add_argument('--users_summary', action='store_true', help='Show the summary stats for each user.')
    # todo: probably use some other temp folder
    parser.add_argument('-o', '--output_path', type=str, required=False, default=PATH_ROOT,
                        help='Personal Auth token needed for higher API request limit.')
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
    host = init_host(args)
    if not host:
        exit('No repository specified.')

    host.fetch_data(args.offline)
    if not args.offline and host.outdated > 0:
        exit('The update failed to complete, pls try it again or run offline.')

    logging.info('Process requested stats...')
    if args.users_summary:
        host.show_users_summary()


def cli_main():
    logging.basicConfig(level=logging.INFO)
    logging.info('running...')
    main(get_arguments())
    logging.info('Done :]')


if __name__ == '__main__':
    cli_main()
