"""
Copyright (C) 2020-2021 Jiri Borovec <...>

Module for collecting star information about dependent repositories.
"""

import logging
import os
from typing import Optional

import pandas as pd
import requests
from bs4 import BeautifulSoup
from tqdm.auto import tqdm

PATH_ROOT = os.path.dirname(os.path.dirname(__file__))


def collect_dependents_stars(
    github_repo: str,
    scope: str = "REPOSITORY",
    output_path: str = PATH_ROOT,
    output_filename: Optional[str] = None,
):
    """Collect star information about repositories that depend on the given repository.

    Args:
        github_repo: GitHub repository in format <owner>/<name>.
        scope: Type of dependents to collect. Either "REPOSITORY" or "PACKAGE".
        output_path: Path to output directory.
        output_filename: Optional custom filename for the output CSV. If not provided,
            generates a name based on repository and scope.

    """
    url = f"https://github.com/{github_repo}/network/dependents?dependent_type={scope}"
    fetching = []

    logging.info(f"Collecting dependents for {github_repo} (scope: {scope})")
    pbar = tqdm(desc="Fetching pages...")

    while True:
        try:
            dep = requests.get(url, timeout=10)
            dep.raise_for_status()
        except requests.RequestException as e:
            logging.error(f"Failed to fetch {url}: {e}")
            break

        html = dep.content.decode(dep.encoding)
        soup = BeautifulSoup(html, "html.parser")

        # Extract repository information from the page
        boxes = soup.findAll("div", {"class": "Box-row"})
        if not boxes:
            logging.warning(f"No Box-row elements found on page: {url}")

        page = []
        for box in boxes:
            try:
                org_elem = box.find("a", {"data-repository-hovercards-enabled": ""})
                repo_elem = box.find("a", {"data-hovercard-type": "repository"})
                star_fork_elems = box.find_all("span", {"class": "pl-3"})

                if org_elem and repo_elem and len(star_fork_elems) >= 2:
                    page.append(
                        {
                            "org": org_elem.text,
                            "repo": repo_elem.text,
                            "stars": int(star_fork_elems[0].text.replace(",", "")),
                            "forks": int(star_fork_elems[1].text.replace(",", "")),
                        }
                    )
            except (AttributeError, ValueError, IndexError) as e:
                logging.warning(f"Failed to parse box element: {e}")
                continue

        # Check for pagination
        pagination = soup.find("div", {"class": "paginate-container"})
        if not pagination:
            # No pagination means this is likely the last/only page
            fetching += page
            logging.info("No pagination found, this is the last page")
            break

        fetching += page
        nav_hrefs = pagination.find_all("a")

        # Check if there's a "next" link
        if not nav_hrefs or "next" not in [href.text.lower() for href in nav_hrefs]:
            break

        # Get the next page URL (GitHub uses relative URLs)
        next_href = nav_hrefs[-1].get("href")
        if not next_href:
            logging.warning("Next link found but no href attribute")
            break

        # Convert relative URL to absolute URL
        url = f"https://github.com{next_href}" if next_href.startswith("/") else next_href

        pbar.update()

    pbar.close()

    logging.info(f"Collected {len(fetching)} dependents")

    if not fetching:
        logging.warning("No dependents found")
        return

    # Create DataFrame and sort by stars
    stats = pd.DataFrame(fetching).sort_values("stars", ascending=False)
    stats["URL"] = [f"https://github.com/{row['org']}/{row['repo']}" for _, row in stats.iterrows()]

    # Generate output filename
    if output_filename is None:
        output_filename = f"dependents-{github_repo.replace('/', '-')}-{scope}.csv"

    output_file = os.path.join(output_path, output_filename)

    # Remove duplicates and save to CSV
    stats.drop_duplicates().to_csv(output_file, index=None)
    logging.info(f"Results saved to {output_file}")
