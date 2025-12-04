"""
Copyright (C) 2020-2021 Jiri Borovec <...>
"""

import logging

from repo_stats.cli import analyze, scrape, stars

# Command structure for jsonargparse
commands = {
    "scrape": scrape,
    "analyze": analyze,
    "stars": stars,
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
