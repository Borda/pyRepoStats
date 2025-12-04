"""Tests for dependents functionality."""

import json
from pathlib import Path
from unittest import mock

import pytest

from repo_stats.dependents import fetch_dependents, process_dependents


@pytest.fixture
def mock_dependents_html():
    """Mock HTML response for dependents page."""
    return """
    <html>
        <div class="Box-row">
            <a data-repository-hovercards-enabled="">test-org</a>
            <a data-hovercard-type="repository">test-repo</a>
            <span class="pl-3">100</span>
            <span class="pl-3">20</span>
        </div>
        <div class="Box-row">
            <a data-repository-hovercards-enabled="">another-org</a>
            <a data-hovercard-type="repository">another-repo</a>
            <span class="pl-3">50</span>
            <span class="pl-3">10</span>
        </div>
        <div class="paginate-container">
        </div>
    </html>
    """


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
def test_fetch_dependents_with_mock(mock_dependents_html, dependent_type):
    """Test fetching dependents with mocked requests."""
    with mock.patch("repo_stats.dependents.requests.get") as mock_get:
        mock_response = mock.Mock()
        mock_response.content = mock_dependents_html.encode("utf-8")
        mock_response.encoding = "utf-8"
        mock_response.raise_for_status = mock.Mock()
        mock_get.return_value = mock_response

        result = fetch_dependents("owner/repo", dependent_type=dependent_type, timeout=10)

        assert len(result) == 2
        assert result[0]["org"] == "test-org"
        assert result[0]["repo"] == "test-repo"
        assert result[0]["stars"] == 100
        assert result[0]["forks"] == 20
        assert result[0]["url"] == "https://github.com/test-org/test-repo"


def test_fetch_dependents_handles_errors():
    """Test that fetch_dependents handles request errors gracefully."""
    with mock.patch("repo_stats.dependents.requests.get") as mock_get:
        mock_get.side_effect = Exception("Network error")

        result = fetch_dependents("owner/repo", max_retries=1, retry_delay=0)

        # Should return empty list on error
        assert result == []
