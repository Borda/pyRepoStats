"""
Copyright (C) 2020-2021 Jiri Borovec <...>

Module for fetching repository dependents (projects that depend on this repository).
"""

import logging
import time

import pandas as pd
import requests
from bs4 import BeautifulSoup
from tqdm import tqdm


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
    fetching = []

    with tqdm(desc=f"Fetching {dependent_type.lower()} dependents") as pbar:
        retries = 0
        while True:
            try:
                dep = requests.get(url, timeout=timeout)
                dep.raise_for_status()
                html = dep.content.decode(dep.encoding)
                soup = BeautifulSoup(html, "html.parser")

                # Parse page items
                page = []
                for box in soup.findAll("div", {"class": "Box-row"}):
                    try:
                        org_elem = box.find("a", {"data-repository-hovercards-enabled": ""})
                        repo_elem = box.find("a", {"data-hovercard-type": "repository"})
                        star_elems = box.find_all("span", {"class": "pl-3"})

                        if org_elem and repo_elem and len(star_elems) >= 2:
                            org = org_elem.text.strip()
                            repo = repo_elem.text.strip()
                            stars = int(star_elems[0].text.replace(",", "").strip())
                            forks = int(star_elems[1].text.replace(",", "").strip())

                            page.append(
                                {
                                    "org": org,
                                    "repo": repo,
                                    "stars": stars,
                                    "forks": forks,
                                    "url": f"https://github.com/{org}/{repo}",
                                }
                            )
                    except (AttributeError, ValueError, IndexError) as e:
                        logging.debug(f"Failed to parse dependent item: {e}")
                        continue

                # Check for pagination
                pagination = soup.find("div", {"class": "paginate-container"})
                if not pagination:
                    logging.debug(f"No pagination found on page: {url}")
                    if retries < max_retries:
                        retries += 1
                        logging.warning(f"Retrying in {retry_delay} seconds (attempt {retries}/{max_retries})")
                        time.sleep(retry_delay)
                        continue
                    logging.warning(f"Max retries reached, stopping: {url}")
                    break

                fetching += page
                pbar.update(len(page))

                # Check for next page - find the anchor with "next" text
                nav_hrefs = pagination.find_all("a")
                next_link = None
                for href in nav_hrefs:
                    if href.text.lower().strip() == "next":
                        next_link = href.get("href")
                        break

                if not next_link:
                    break

                # Convert relative URL to absolute URL if needed
                url = f"https://github.com{next_link}" if next_link.startswith("/") else next_link

                # Reset retries on successful page fetch
                retries = 0

            except requests.RequestException as e:
                logging.error(f"Request failed for {url}: {e}")
                if retries < max_retries:
                    retries += 1
                    logging.warning(f"Retrying in {retry_delay} seconds (attempt {retries}/{max_retries})")
                    time.sleep(retry_delay)
                else:
                    logging.error("Max retries reached, stopping")
                    break
            except Exception as e:
                logging.error(f"Unexpected error fetching dependents: {e}")
                break

    logging.info(f"Fetched {len(fetching)} {dependent_type.lower()} dependents")
    return fetching


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
