# Getting started

## Installation

The package is not on PyPI yet, install it straight from GitHub:

```bash
pip install https://github.com/Borda/pyRepoStats/archive/main.zip
```

or from a clone, which is also the way to develop it:

```bash
git clone https://github.com/Borda/pyRepoStats.git
cd pyRepoStats
pip install -e .
```

Python 3.12 or newer is required.

## Quick start

```bash
# 1. log in once, repostat picks the session up automatically
gh auth login

# 2. download the repository data (needs internet)
mkdir -p ./stats
repostat scrape Borda/pyRepoStats --output_path ./stats

# 3. analyze the cache (works offline)
repostat analyze Borda/pyRepoStats --output_path ./stats --users_summary+ "merged PRs" --user_comments+ M
```

`python -m repo_stats <command> <repository> [options]` is the same CLI. Always pass `--output_path`, otherwise caches and results land in the installation folder, most likely _site-packages_.

## Running in GitHub Actions

The built-in token is enough for public repositories:

```yaml
- run: |
    mkdir -p ./stats
    repostat scrape ${{ github.repository }} --output_path ./stats
  env:
    GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```
