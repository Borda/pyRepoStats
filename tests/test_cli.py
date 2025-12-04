import os
import shutil
from pathlib import Path
from unittest import mock

import pytest

from repo_stats.__main__ import cli_main


@pytest.fixture
def temp_output_with_cache(tmp_path):
    """Create a temporary output directory with cached test data."""
    # Copy the fixture data to the temp directory
    fixture_file = Path(__file__).parent / "fixtures" / "dump-github_Borda-pyRepoStats.json"
    if fixture_file.exists():
        shutil.copy(fixture_file, tmp_path / "dump-github_Borda-pyRepoStats.json")
    return str(tmp_path)


@pytest.mark.parametrize(
    "cli_args",
    [
        # The + suffix (e.g., --users_summary+, --user_comments+) is jsonargparse syntax
        # for appending to list arguments. It allows passing multiple values:
        # --user_comments+ D --user_comments+ W (creates list ["D", "W"])
        '--min_contribution 2 --users_summary+ "all"',
        "--min_contribution 2 --user_comments+ D",
        "--min_contribution 1 --user_comments+ W",
        "--min_contribution 1 --user_comments+ W --user_comments+ issue",
        "--min_contribution 1 --user_comments+ D --user_comments+ W --user_comments+ pr",
    ],
)
def test_offline_github(cli_args, temp_output_with_cache):
    """Test CLI with offline mode using cached data."""
    full_args = f"analyze Borda/pyRepoStats --output_path {temp_output_with_cache} {cli_args}"
    with (
        mock.patch("argparse._sys.argv", ["any.py"] + full_args.strip().split()),
        mock.patch("repo_stats.cli.SHOW_FIGURES", False),
    ):
        cli_main()


@pytest.mark.skipif(
    not os.getenv("GH_API_TOKEN"),
    reason="requires GH_API_TOKEN environment variable for online tests",
)
@pytest.mark.parametrize(
    "cli_args",
    [
        "Borda/pyRepoStats",
    ],
)
def test_online_github(cli_args, tmp_path):
    """Test CLI with online mode (requires token)."""
    full_args = f"scrape {cli_args} --output_path {tmp_path}"
    with (
        mock.patch("argparse._sys.argv", ["any.py"] + full_args.strip().split()),
        mock.patch("repo_stats.cli.SHOW_FIGURES", False),
    ):
        cli_main()
