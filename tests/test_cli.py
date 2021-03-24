from unittest import mock

import pytest

from repostats.cli import cli_main


@pytest.mark.xfail(reason="offline or reached free requests limit")
@pytest.mark.parametrize(
    'cli_args', [
        '-gh Borda/pyRepoStats',
        '-gh Borda/pyRepoStats --offline --min_contribution 2 --users_summary "all"',
        '-gh Borda/pyRepoStats --offline --min_contribution 2 --user_comments D',
        '-gh Borda/pyRepoStats --offline --min_contribution 1 --user_comments W',
        '-gh Borda/pyRepoStats --offline --min_contribution 1 --user_comments W issue',
        '-gh Borda/pyRepoStats --offline --min_contribution 1 --user_comments D W pr',
    ]
)
def test_online_github(cli_args):

    with mock.patch("argparse._sys.argv", ["any.py"] + cli_args.strip().split()):
        cli_main()
