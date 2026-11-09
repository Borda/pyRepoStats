"""
Copyright (C) 2020-2021 Jiri Borovec <...>
"""

import logging

from repo_stats.cli import analyze, fetch_repo_dependents, scrape

# Command structure for jsonargparse
commands = {
    "scrape": scrape,
    "analyze": analyze,
    "fetch_repo_dependents": fetch_repo_dependents,
}


def cli_main():
    """CLI entry point for backward compatibility."""
    logging.basicConfig(level=logging.INFO)
    logging.info("running...")
    from jsonargparse import auto_cli

    auto_cli(commands)
    logging.info("Done :]")


if __name__ == "__main__":
    cli_main()
