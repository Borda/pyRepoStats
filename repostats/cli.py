"""
Copyright (C) 2020-2020 Jiri Borovec <...>
"""

import logging
import os
from argparse import ArgumentParser
from pprint import pformat

from tabulate import tabulate

from repostats.github import github_main
from repostats.stats import compute_users_stat

PATH_ROOT = os.path.dirname(os.path.dirname(__file__))
CSV_USER_SUMMARY = '%s_%s_users-summary.csv'
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
    repo_name = 'any/repo'
    host_name = 'unknown'
    host_user_url = '%(user)s'

    if args.github_repo:
        data = github_main(
            args.github_repo,
            output_path=args.output_path,
            auth_token=args.auth_token,
            offline=args.offline,
        )
        host_name = 'github'
        repo_name = args.github_repo
        host_user_url = '[%(user)s](https://github.com/%(user)s)'
    else:
        exit('No repository specified.')

    if args.user_summary:
        df_users = compute_users_stat(data['items'])
        df_users = df_users[['merged PRs', 'commented PRs', 'opened issues', 'commented issues', 'all opened']]
        df_users.to_csv(os.path.join(args.output_path, CSV_USER_SUMMARY % (host_name, repo_name.replace('/', '-'))))
        df_users.index = df_users.index.map(lambda u: host_user_url % {'user': u})
        print(tabulate(df_users[df_users['all opened'] >= MIN_CONTRIBUTION_COUNT], tablefmt="pipe", headers="keys"))


def cli_main():
    logging.basicConfig(level=logging.INFO)
    logging.info('running...')
    main(get_arguments())
    logging.info('Done :]')


if __name__ == '__main__':
    cli_main()
