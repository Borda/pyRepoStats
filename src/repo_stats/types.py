"""
Copyright (C) 2020-2021 Jiri Borovec <...>

Type definitions and enums for repo_stats.
"""

from enum import Enum


class DependentType(str, Enum):
    """Type of dependents to fetch."""

    REPOSITORY = "REPOSITORY"
    PACKAGE = "PACKAGE"


def parse_dependent_type(type_str: str) -> list[DependentType]:
    """Parse dependent type string into list of DependentType enums.

    Args:
        type_str: String representation of dependent type(s)

    Returns:
        List of DependentType enums

    Example:
        >>> parse_dependent_type("repository")
        [<DependentType.REPOSITORY: 'REPOSITORY'>]
        >>> parse_dependent_type("all")
        [<DependentType.REPOSITORY: 'REPOSITORY'>, <DependentType.PACKAGE: 'PACKAGE'>]
    """
    type_val = type_str.lower()
    if type_val in ("all", "both"):
        return [DependentType.REPOSITORY, DependentType.PACKAGE]
    if type_val in ("repository", "repo", "repositories", "repos"):
        return [DependentType.REPOSITORY]
    if type_val in ("package", "packages", "pkg"):
        return [DependentType.PACKAGE]
    return []
