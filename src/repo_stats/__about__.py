__version__ = "0.2.0dev"
__author__ = "Jiri Borovec"
__author_email__ = "j.borovec@...com"
__license__ = "MIT"
__homepage__ = "https://borda.github.io/pyRepoStats"
__copyright__ = f"Copyright (c) 2020-2023, {__author__}."
__docs__ = "Repository Statistics"
__long_doc__ = (
    f"# {__docs__}"
    + """

This simple tool aims on open-source projects providing simple repository stats
 which are a bit out of scope of base Git and need some more information about issues and PRs.

**Some highlighted features:**
- cumulative caching (no need to full download, just incremental/needed update)
- collection of overall user contributions to issues/PRs
- visualization of aggregated timeline of past contributions
"""
)

__all__ = [
    "__author__",
    "__author_email__",
    "__copyright__",
    "__docs__",
    "__homepage__",
    "__license__",
    "__version__",
]
