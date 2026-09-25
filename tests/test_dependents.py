"""Tests for dependents functionality."""

from unittest import mock

import pytest
from scrapling.engines.toolbelt.custom import Response

from repo_stats.dependents import fetch_dependents, process_dependents


@pytest.fixture
def mock_dependents_html():
    """Mock HTML response for dependents page."""
    return """
    <html>
        <div class="Box-row">
            <a data-hovercard-type="repository" href="/test-org/test-repo">test-repo</a>
            <span class="pl-3">100</span>
            <span class="pl-3">20</span>
        </div>
        <div class="Box-row">
            <a data-hovercard-type="repository" href="/another-org/another-repo">another-repo</a>
            <span class="pl-3">50</span>
            <span class="pl-3">10</span>
        </div>
        <div class="paginate-container">
        </div>
    </html>
    """


@pytest.fixture
def mock_response_factory():
    """Factory for creating Scrapling Response objects from HTML."""

    def _factory(url, html, status=200):
        return Response(
            url=url,
            content=html,
            status=status,
            reason="OK" if status < 400 else "Error",
            cookies={},
            headers={},
            request_headers={},
        )

    return _factory


def test_process_dependents_empty():
    """Test processing empty dependents list."""
    result = process_dependents([])
    assert result.empty


def test_process_dependents_with_data():
    """Test processing dependents with valid data."""
    dependents = [
        {"org": "org1", "repo": "repo1", "stars": 100, "forks": 20, "url": "https://github.com/org1/repo1"},
        {"org": "org2", "repo": "repo2", "stars": 50, "forks": 10, "url": "https://github.com/org2/repo2"},
    ]
    result = process_dependents(dependents)

    assert len(result) == 2
    assert result.iloc[0]["stars"] == 100  # Should be sorted by stars descending
    assert result.iloc[1]["stars"] == 50


def test_process_dependents_removes_duplicates():
    """Test that duplicate URLs are removed."""
    dependents = [
        {"org": "org1", "repo": "repo1", "stars": 100, "forks": 20, "url": "https://github.com/org1/repo1"},
        {"org": "org1", "repo": "repo1", "stars": 100, "forks": 20, "url": "https://github.com/org1/repo1"},
        {"org": "org2", "repo": "repo2", "stars": 50, "forks": 10, "url": "https://github.com/org2/repo2"},
    ]
    result = process_dependents(dependents)

    assert len(result) == 2


@pytest.mark.parametrize("dependent_type", ["REPOSITORY", "PACKAGE"])
def test_fetch_dependents_with_mock(mock_dependents_html, mock_response_factory, dependent_type):
    """Test fetching dependents with mocked Scrapling response."""
    url = f"https://github.com/owner/repo/network/dependents?dependent_type={dependent_type}"
    response = mock_response_factory(url, mock_dependents_html)

    with mock.patch("repo_stats.dependents.Fetcher.get") as mock_get:
        mock_get.return_value = response

        result = fetch_dependents("owner/repo", dependent_type=dependent_type, timeout=10)

        assert len(result) == 2
        assert result[0]["org"] == "test-org"
        assert result[0]["repo"] == "test-repo"
        assert result[0]["stars"] == 100
        assert result[0]["forks"] == 20
        assert result[0]["url"] == "https://github.com/test-org/test-repo"


def test_fetch_dependents_pagination(mock_response_factory):
    """Test that pagination follows the Next link and stops when there is none."""
    page1_html = """
    <html>
        <div class="Box-row">
            <a data-hovercard-type="repository" href="/org1/repo1">repo1</a>
            <span class="pl-3">10</span>
            <span class="pl-3">1</span>
        </div>
        <div class="paginate-container">
            <a href="/owner/repo/network/dependents?dependent_type=REPOSITORY&amp;after=abc">Next</a>
        </div>
    </html>
    """
    page2_html = """
    <html>
        <div class="Box-row">
            <a data-hovercard-type="repository" href="/org2/repo2">repo2</a>
            <span class="pl-3">5</span>
            <span class="pl-3">0</span>
        </div>
        <div class="paginate-container">
            <span>Previous</span>
        </div>
    </html>
    """

    responses = {
        "https://github.com/owner/repo/network/dependents?dependent_type=REPOSITORY": mock_response_factory(
            "https://github.com/owner/repo/network/dependents?dependent_type=REPOSITORY", page1_html
        ),
        "https://github.com/owner/repo/network/dependents?dependent_type=REPOSITORY&after=abc": mock_response_factory(
            "https://github.com/owner/repo/network/dependents?dependent_type=REPOSITORY&after=abc", page2_html
        ),
    }

    with mock.patch("repo_stats.dependents.Fetcher.get") as mock_get:
        mock_get.side_effect = lambda url, **kwargs: responses[url]

        result = fetch_dependents("owner/repo", dependent_type="REPOSITORY", timeout=10)

        assert len(result) == 2
        assert result[0]["org"] == "org1"
        assert result[1]["org"] == "org2"


def test_fetch_dependents_no_pagination_container(mock_response_factory):
    """Test that a page without pagination container is treated as the only page."""
    html = """
    <html>
        <div class="Box-row">
            <a data-hovercard-type="repository" href="/org1/repo1">repo1</a>
            <span class="pl-3">10</span>
            <span class="pl-3">1</span>
        </div>
    </html>
    """
    response = mock_response_factory(
        "https://github.com/owner/repo/network/dependents?dependent_type=REPOSITORY", html
    )

    with mock.patch("repo_stats.dependents.Fetcher.get") as mock_get:
        mock_get.return_value = response

        result = fetch_dependents("owner/repo", dependent_type="REPOSITORY", timeout=10)

        assert len(result) == 1


def test_fetch_dependents_handles_errors():
    """Test that fetch_dependents handles request errors gracefully."""
    with mock.patch("repo_stats.dependents._fetch_page") as mock_fetch:
        mock_fetch.return_value = None

        result = fetch_dependents("owner/repo", max_retries=1, retry_delay=0)

        # Should return empty list on error
        assert result == []
