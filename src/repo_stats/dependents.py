"""
Copyright (C) 2020-2021 Jiri Borovec <...>

Module for fetching repository dependents (projects that depend on this repository).
"""

import logging
import time
from dataclasses import dataclass

import pandas as pd
import requests
from bs4 import BeautifulSoup
from tqdm import tqdm


@dataclass
class DependentRepo:
    """Information about a dependent repository."""

    org: str
    repo: str
    stars: int
    forks: int

    @property
    def url(self) -> str:
        """Get the full GitHub URL."""
        return f"https://github.com/{self.org}/{self.repo}"

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "org": self.org,
            "repo": self.repo,
            "stars": self.stars,
            "forks": self.forks,
            "url": self.url,
        }


def _parse_dependent_box(box) -> DependentRepo | None:
    """Parse a single dependent box from HTML.

    Args:
        box: BeautifulSoup element containing dependent information

    Returns:
        DependentRepo instance or None if parsing fails
    """
    try:
        org_elem = box.find("a", {"data-repository-hovercards-enabled": ""})
        repo_elem = box.find("a", {"data-hovercard-type": "repository"})
        star_elems = box.find_all("span", {"class": "pl-3"})

        if org_elem and repo_elem and len(star_elems) >= 2:
            org = org_elem.text.strip()
            repo = repo_elem.text.strip()
            stars = int(star_elems[0].text.replace(",", "").strip())
            forks = int(star_elems[1].text.replace(",", "").strip())

            return DependentRepo(org=org, repo=repo, stars=stars, forks=forks)
    except (AttributeError, ValueError, IndexError) as e:
        logging.debug(f"Failed to parse dependent item: {e}")

    return None


def _parse_page_dependents(soup: BeautifulSoup) -> list[DependentRepo]:
    """Parse all dependents from a page.

    Args:
        soup: BeautifulSoup object of the page

    Returns:
        List of DependentRepo instances
    """
    dependents = []
    for box in soup.findAll("div", {"class": "Box-row"}):
        dependent = _parse_dependent_box(box)
        if dependent:
            dependents.append(dependent)
    return dependents


def _find_next_page_url(soup: BeautifulSoup) -> str | None:
    """Find the URL for the next page of results.

    Args:
        soup: BeautifulSoup object of the current page

    Returns:
        URL string for next page or None if no next page
    """
    pagination = soup.find("div", {"class": "paginate-container"})
    if not pagination:
        return None

    nav_hrefs = pagination.find_all("a")
    for href in nav_hrefs:
        if href.text.lower().strip() == "next":
            next_link = href.get("href")
            if next_link:
                # Convert relative URL to absolute URL if needed
                return f"https://github.com{next_link}" if next_link.startswith("/") else next_link

    return None


def _fetch_page(url: str, timeout: int) -> BeautifulSoup | None:
    """Fetch and parse a single page.

    Args:
        url: URL to fetch
        timeout: Request timeout in seconds

    Returns:
        BeautifulSoup object or None if request fails
    """
    try:
        response = requests.get(url, timeout=timeout)
        response.raise_for_status()
        html = response.content.decode(response.encoding)
        return BeautifulSoup(html, "html.parser")
    except requests.RequestException as e:
        logging.error(f"Request failed for {url}: {e}")
        return None


def fetch_dependents(
    repo_name: str,
    dependent_type: str = "REPOSITORY",
    timeout: int = 10,
    max_retries: int = 3,
    retry_delay: int = 9,
) -> list[dict]:
    """Fetch list of repositories that depend on the given repository.

    Args:
        repo_name: Repository name in format 'owner/repo'
        dependent_type: Type of dependents - 'REPOSITORY' or 'PACKAGE'
        timeout: Request timeout in seconds
        max_retries: Maximum number of retries for failed requests
        retry_delay: Delay in seconds before retrying

    Returns:
        List of dictionaries containing dependent repository information with keys:
        - org: Organization/owner name
        - repo: Repository name
        - stars: Number of stars
        - forks: Number of forks
        - url: Full GitHub URL

    Example:
        >>> deps = fetch_dependents("octocat/Hello-World", dependent_type="REPOSITORY")
        >>> isinstance(deps, list)
        True
    """
    url = f"https://github.com/{repo_name}/network/dependents?dependent_type={dependent_type}"
    all_dependents = []
    retries = 0

    pbar = tqdm(desc=f"Fetching {dependent_type.lower()} dependents")

    while url:
        soup = _fetch_page(url, timeout)

        if not soup:
            if retries < max_retries:
                retries += 1
                logging.warning(f"Retrying in {retry_delay} seconds (attempt {retries}/{max_retries})")
                time.sleep(retry_delay)
                continue
            logging.error("Max retries reached, stopping")
            break

        # Parse dependents from current page
        page_dependents = _parse_page_dependents(soup)
        all_dependents.extend(page_dependents)
        pbar.update(len(page_dependents))

        # Reset retries on successful fetch
        retries = 0

        # Find next page URL
        url = _find_next_page_url(soup)

    pbar.close()

    logging.info(f"Fetched {len(all_dependents)} {dependent_type.lower()} dependents")
    return [dep.to_dict() for dep in all_dependents]


def process_dependents(dependents: list[dict]) -> pd.DataFrame:
    """Process and sort dependents data.

    Args:
        dependents: List of dependent dictionaries from fetch_dependents

    Returns:
        DataFrame with dependents sorted by stars (descending), with duplicates removed

    Example:
        >>> deps = [{"org": "foo", "repo": "bar", "stars": 10, "forks": 5, "url": "https://github.com/foo/bar"}]
        >>> df = process_dependents(deps)
        >>> len(df)
        1
    """
    if not dependents:
        return pd.DataFrame()

    df = pd.DataFrame(dependents)
    df = df.sort_values("stars", ascending=False)
    return df.drop_duplicates(subset=["url"])
