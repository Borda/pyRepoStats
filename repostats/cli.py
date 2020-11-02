"""
Copyright (C) 2020-2020 Jiri Borovec <...>
"""

import logging
import os
from argparse import ArgumentParser
from pprint import pformat

from repostats.github import GitHub

PATH_ROOT = os.path.dirname(os.path.dirname(__file__))
MIN_CONTRIBUTION_COUNT = 3


def get_arguments():
    parser = ArgumentParser('Parse Repository details')
    parser.add_argument('-gh', '--github_repo', type=str, required=False, default=None,
                        help='GitHub repository in format <owner>/<name>.')
    parser.add_argument('-t', '--auth_token', type=str, required=False, default=None,
                        help='Personal Auth token needed for higher API request limit')
    parser.add_argument('--offline', action='store_true', help='Skip updating all information from web.')
    parser.add_argument('--user_summary', action='store_true', help='Show the summary stats for each user.')
    # todo: probably use some other temp folder
    parser.add_argument('-o', '--output_path', type=str, required=False, default=PATH_ROOT,
                        help='Personal Auth token needed for higher API request limit.')
    args = parser.parse_args()
    logging.info('Parsed arguments: \n%s', pformat(vars(args)))
    return args


def main(args):
    """Main entry point."""
    if args.github_repo:
        host = GitHub(
            args.github_repo,
            output_path=args.output_path,
            auth_token=args.auth_token,
        )
    else:
        host = None
        exit('No repository specified.')

    host.fetch_data(args.offline)

    if args.user_summary:
        host.show_user_summary()


def cli_main():
    logging.basicConfig(level=logging.INFO)
    logging.info('running...')
    main(get_arguments())
    logging.info('Done :]')


if __name__ == '__main__':
    cli_main()
