from unittest import mock

import pytest

from repo_stats.github import GitHub

_ENV_NAMES = ("GH_API_TOKEN", "GITHUB_TOKEN", "GH_TOKEN")


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch):
    for name in _ENV_NAMES:
        monkeypatch.delenv(name, raising=False)


def _gh_cli(stdout="cli-token\n", returncode=0):
    return mock.patch(
        "repo_stats.github.subprocess.run",
        return_value=mock.Mock(stdout=stdout, returncode=returncode),
    )


def test_token_priority(tmp_path, monkeypatch):
    """Explicit argument beats env variables, which beat the `gh` CLI."""
    monkeypatch.setenv("GITHUB_TOKEN", "from-github-token")
    with _gh_cli() as run:
        assert GitHub("a/b", str(tmp_path), auth_token="explicit").auth_token == "explicit"
        assert GitHub("a/b", str(tmp_path)).auth_token == "from-github-token"
        run.assert_not_called()

    monkeypatch.setenv("GH_API_TOKEN", "from-api-token")
    assert GitHub("a/b", str(tmp_path)).auth_token == "from-api-token"


def test_token_from_gh_cli(tmp_path):
    with _gh_cli() as run, mock.patch("repo_stats.github.shutil.which", return_value="/usr/bin/gh"):
        assert GitHub("a/b", str(tmp_path)).auth_token == "cli-token"
    # the token must travel through a pipe only: never on argv, never via a shell
    args, kwargs = run.call_args
    assert args[0] == ["/usr/bin/gh", "auth", "token", "--hostname", "github.com"]
    assert not kwargs.get("shell")


@pytest.mark.parametrize("which", [None, "/usr/bin/gh"])
def test_token_cli_unavailable(tmp_path, which):
    """Missing `gh` or a logged-out `gh` falls back to anonymous access."""
    with (
        _gh_cli(stdout="", returncode=1),
        mock.patch("repo_stats.github.shutil.which", return_value=which),
    ):
        assert GitHub("a/b", str(tmp_path)).auth_token is None
