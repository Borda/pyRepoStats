"""
Copyright (C) 2020-2021 Jiri Borovec <...>

Module for fetching repository dependents (projects that depend on this repository).
"""

import logging
from dataclasses import dataclass

import pandas as pd
from scrapling import Selector
from scrapling.fetchers import Fetcher
from tqdm import tqdm


@dataclass(frozen=True)
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


def _parse_dependent_box(box: Selector) -> DependentRepo | None:
    """Parse a single dependent box from HTML.

    Args:
        box: Scrapling selector containing dependent information

    Returns:
        DependentRepo instance or None if parsing fails
    """
    try:
        repo_elem = box.css("a[data-hovercard-type='repository']")[0]
        href = repo_elem.attrib.get("href", "").strip("/")
        if "/" not in href:
            return None
        org, repo = href.split("/", 1)

        star_elems = box.css("span.pl-3")
        if len(star_elems) < 2:
            return None
        stars = int(star_elems[0].text.replace(",", "").strip())
        forks = int(star_elems[1].text.replace(",", "").strip())

        return DependentRepo(org=org, repo=repo, stars=stars, forks=forks)
    except (AttributeError, IndexError, ValueError) as e:
        logging.debug(f"Failed to parse dependent item: {e}")

    return None


def _parse_page_dependents(page: Selector) -> list[DependentRepo]:
    """Parse all dependents from a page.

    Args:
        page: Scrapling selector of the page

    Returns:
        List of DependentRepo instances
    """
    dependents = []
    for box in page.css("div.Box-row"):
        dependent = _parse_dependent_box(box)
        if dependent:
            dependents.append(dependent)
    return dependents


def _find_next_page_url(page: Selector, base_url: str) -> str | None:
    """Find the URL for the next page of results.

    Args:
        page: Scrapling selector of the current page
        base_url: Base URL used to resolve relative links

    Returns:
        URL string for next page or None if no next page
    """
    pagination = page.css("div.paginate-container")
    if not pagination:
        return None

    for link in pagination[0].css("a"):
        if link.text.lower().strip() == "next":
            next_link = link.attrib.get("href")
            if next_link:
                return page.urljoin(next_link) if next_link.startswith("/") else next_link

    return None


def _fetch_page(url: str, timeout: int) -> Selector | None:
    """Fetch and parse a single page.

    Args:
        url: URL to fetch
        timeout: Request timeout in seconds

    Returns:
        Scrapling selector or None if request fails
    """
    try:
        response = Fetcher.get(url, timeout=timeout, retries=1)
        if response.status >= 400:
            logging.error(f"Request failed for {url} with status {response.status}")
            return None
        return response
    except Exception as e:
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
        >>> deps = fetch_dependents("octocat/Hello-World", dependent_type="REPOSITORY")  # doctest: +SKIP
        >>> isinstance(deps, list)  # doctest: +SKIP
        True
    """
    url = f"https://github.com/{repo_name}/network/dependents?dependent_type={dependent_type}"
    all_dependents = []
    retries = 0

    pbar = tqdm(desc=f"Fetching {dependent_type.lower()} dependents")

    while url:
        page = _fetch_page(url, timeout)

        if page is None:
            if retries < max_retries:
                retries += 1
                logging.warning(f"Retrying in {retry_delay} seconds (attempt {retries}/{max_retries})")
                continue
            logging.error("Max retries reached, stopping")
            break

        # Parse dependents from current page
        page_dependents = _parse_page_dependents(page)
        all_dependents.extend(page_dependents)
        pbar.update(len(page_dependents))

        # Reset retries on successful fetch
        retries = 0

        # Find next page URL
        url = _find_next_page_url(page, url)

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
    # Keep the most starred repo for each unique URL (sorted descending by stars)
    return df.drop_duplicates(subset=["url"], keep="first")
