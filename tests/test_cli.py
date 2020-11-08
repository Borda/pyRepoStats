from unittest import mock

import pytest

from repostats.cli import cli_main


@pytest.mark.xfail(reason="offline or reached free requests limit")
@pytest.mark.parametrize('cli_args', [
    '-gh Borda/pyRepoStats',
    '-gh Borda/pyRepoStats --offline --users_summary "all"',
    '-gh Borda/pyRepoStats --offline --user_comments W --min_contribution 2',
    '-gh Borda/pyRepoStats --offline --user_comments Y',
])
def test_online_github(cli_args):

    with mock.patch("argparse._sys.argv", ["any.py"] + cli_args.strip().split()):
        cli_main()
