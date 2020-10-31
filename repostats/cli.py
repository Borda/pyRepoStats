"""
Copyright (C) 2020-2020 Jiri Borovec <...>
"""

import logging
import os
from argparse import ArgumentParser
from typing import Optional
from pprint import pformat

from repostats.github import github_main

PATH_ROOT = os.path.dirname(os.path.dirname(__file__))


def get_arguments():
    parser = ArgumentParser('Parse Repository details')
    parser.add_argument('-gh', '--github_repo', type=str, required=False, default=None,
                        help='GitHub repository in format <owner>/<name>')
    parser.add_argument('-t', '--auth_token', type=str, required=False, default=None,
                        help='Personal Auth token needed for higher API request limit')
    parser.add_argument('--offline', action='store_true', help='Skip updating all information from web')
    # todo: probably use some other temp folder
    parser.add_argument('-o', '--output_path', type=str, required=False, default=PATH_ROOT,
                        help='Personal Auth token needed for higher API request limit')
    args = vars(parser.parse_args())
    logging.info('Parsed arguments: \n%s', pformat(args))
    return args


def main(github_repo: Optional[str], output_path: str, auth_token: Optional[str] = None, offline: bool = False):
    """Main entry point."""
    if github_repo:
        github_main(github_repo, output_path=output_path, auth_token=auth_token, offline=offline)
    else:
        exit('No repository specified.')


def cli_main():
    logging.basicConfig(level=logging.INFO)
    logging.info('running...')
    main(**get_arguments())
    logging.info('Done :]')


if __name__ == '__main__':
    cli_main()
