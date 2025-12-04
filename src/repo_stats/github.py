"""
Copyright (C) 2020-2021 Jiri Borovec <...>
"""

import logging
import warnings
from typing import Optional

import pandas as pd
from github import Github, GithubException
from tqdm import tqdm

from repo_stats.host import Host


class GitHub(Host):
    """Specific implementation for GitHub host.

    see: https://docs.github.com/en/free-pro-team@latest/rest/overview/endpoints-available-for-github-apps
    """

    #: host name, server
    HOST_NAME = "github"
    #: if host provides direct link to user
    USER_URL_TEMPLATE = "[%(user)s](https://github.com/%(user)s)"
    #: name to the host
    URL_API = "https://api.github.com/repos"
    #: OS env. variable for getting Token
    OS_ENV_AUTH_TOKEN = "GH_API_TOKEN"
    #: if you have reached the number of free/allowed requests
    API_LIMIT_REACHED = False
    #: hint/explanation what happened
    API_LIMIT_MESSAGE = """
Request failed, probably you have reached free/personal request's limit...
To use higher limit generate personal auth token, see https://developer.github.com/v3/#rate-limiting
"""
    #: define bot users as name pattern
    USER_BOTS = (
        "codecov",
        "pep8speaks",
        "stale",
        "[bot]",
    )
    #: Wait time for URL reply in seconds
    REQUEST_TIMEOUT = 15

    def __init__(
        self,
        repo_name: str,
        output_path: str,
        auth_token: Optional[str] = None,
        min_contribution: int = 3,
    ):
        super().__init__(
            repo_name=repo_name,
            output_path=output_path,
            auth_token=auth_token,
            min_contribution=min_contribution,
        )
        # Initialize PyGithub client
        if auth_token:
            self.github_client = Github(auth_token, timeout=self.REQUEST_TIMEOUT)
        else:
            self.github_client = Github(timeout=self.REQUEST_TIMEOUT)
        self.repo = None

    def _fetch_info(self) -> dict:
        """Download general package info."""
        try:
            if self.repo is None:
                self.repo = self.github_client.get_repo(self.repo_name)

            # Return basic repository information
            return {
                'name': self.repo.name,
                'full_name': self.repo.full_name,
                'description': self.repo.description,
                'stargazers_count': self.repo.stargazers_count,
                'forks_count': self.repo.forks_count,
                'open_issues_count': self.repo.open_issues_count,
            }
        except GithubException as e:
            logging.error(f"Failed to fetch repo info: {e}")
            return {}

    def _fetch_overview(self) -> list[dict]:
        """Fetch all issues from a given repo using listing per pages."""
        items = []
        try:
            if self.repo is None:
                self.repo = self.github_client.get_repo(self.repo_name)

            # Get all issues (includes PRs)
            issues = self.repo.get_issues(state='all')
            total = issues.totalCount

            with tqdm(desc="Requesting issue/PR overview", total=total) as pbar:
                for issue in issues:
                    # Convert PyGithub Issue object to dict format
                    item = {
                        'number': issue.number,
                        'html_url': issue.html_url,
                        'url': issue.url,
                        'state': issue.state,
                        'title': issue.title,
                        'user': {'login': issue.user.login} if issue.user else {'login': 'unknown'},
                        'created_at': issue.created_at.isoformat() if issue.created_at else None,
                        'updated_at': issue.updated_at.isoformat() if issue.updated_at else None,
                        'closed_at': issue.closed_at.isoformat() if issue.closed_at else None,
                        'comments': issue.comments,  # This is just the count initially
                        'comments_url': issue.comments_url,
                    }

                    # Add PR-specific fields if it's a pull request
                    if issue.pull_request:
                        item['pull_request'] = {
                            'url': issue.pull_request.url,
                            'html_url': issue.pull_request.html_url,
                        }
                        # Will need to fetch review comments URL later
                        item['review_comments_url'] = issue.pull_request.url.replace('pulls', 'issues') + '/comments'

                    items.append(item)
                    pbar.update(1)

        except GithubException as e:
            if e.status == 403:
                logging.error(self.API_LIMIT_MESSAGE)
                exit(self.API_LIMIT_MESSAGE)
            raise

        return items

    def _request_comments(self, issue_number: int) -> Optional[list]:
        """Request all comments from the issue life-time."""
        if GitHub.API_LIMIT_REACHED:
            return None
        try:
            if self.repo is None:
                self.repo = self.github_client.get_repo(self.repo_name)

            issue = self.repo.get_issue(issue_number)
            comments = []
            for comment in issue.get_comments():
                comments.append({
                    'user': {'login': comment.user.login} if comment.user else {'login': 'unknown'},
                    'body': comment.body,
                    'created_at': comment.created_at.isoformat() if comment.created_at else None,
                    'updated_at': comment.updated_at.isoformat() if comment.updated_at else None,
                })
            return comments
        except GithubException as e:
            if e.status == 403:
                GitHub.API_LIMIT_REACHED = True
            return None

    def _request_detail_pr(self, pr_number: int) -> Optional[dict]:
        """Request PR status, in particular we want to distinguish between closed and merged ones."""
        if GitHub.API_LIMIT_REACHED:
            return None
        try:
            if self.repo is None:
                self.repo = self.github_client.get_repo(self.repo_name)

            pr = self.repo.get_pull(pr_number)
            return {
                'state': 'merged' if pr.merged else pr.state,
                'merged_at': pr.merged_at.isoformat() if pr.merged_at else None,
                'url': pr.url,
                'html_url': pr.html_url,
            }
        except GithubException as e:
            if e.status == 403:
                GitHub.API_LIMIT_REACHED = True
            return None

    def _update_detail(self, idx_item: tuple[int, dict]) -> tuple:
        """Get all needed issue/PR details"""
        idx, item = idx_item
        # this request is need only for PR, can be skipped for issues
        if "pull" in item["html_url"].split("/"):
            detail = self._request_detail_pr(item["number"])
            if detail is None:
                return idx, None
            item.update(detail)
            # pull review comments for PRs
            r_comments = self._request_review_comments(item["number"])
        else:
            r_comments = []
        extras = {
            # pull all comments
            "comments": self._request_comments(item["number"]),
            "review_comments": r_comments,
        }
        if any(dl is None for dl in extras.values()):
            return idx, None
        # update info
        item.update(extras)
        return idx, item

    def _request_review_comments(self, pr_number: int) -> Optional[list]:
        """Request all review comments from a pull request."""
        if GitHub.API_LIMIT_REACHED:
            return None
        try:
            if self.repo is None:
                self.repo = self.github_client.get_repo(self.repo_name)

            pr = self.repo.get_pull(pr_number)
            review_comments = []
            for comment in pr.get_review_comments():
                review_comments.append({
                    'user': {'login': comment.user.login} if comment.user else {'login': 'unknown'},
                    'body': comment.body,
                    'created_at': comment.created_at.isoformat() if comment.created_at else None,
                    'updated_at': comment.updated_at.isoformat() if comment.updated_at else None,
                })
            return review_comments
        except GithubException as e:
            if e.status == 403:
                GitHub.API_LIMIT_REACHED = True
            return None

    @staticmethod
    def __update_issues_queue(issues: dict[str, dict], issues_new: dict[str, dict]) -> list[str]:
        return [
            idx
            for idx in issues_new
            if (
                idx not in issues
                or not issues[idx]["updated_at"]
                or _dt_update(issues_new, idx) > _dt_update(issues, idx)
            )
        ]

    def _update_details(self, issues: dict[str, dict], issues_new: dict[str, dict]) -> dict[str, dict]:
        """Pull all exiting details to particular issues."""
        # filter missing issue or issues which was updated since last time
        queue = self.__update_issues_queue(issues, issues_new)
        if not queue:
            logging.info("All issues/PRs are up-to-date")
            return issues

        _queue = [(i, issues_new[i]) for i in queue]

        # Process items sequentially with PyGithub (avoid multiprocessing complexity with instance methods)
        for idx_item in tqdm(_queue, desc="Fetching/update details"):
            idx, item = self._update_detail(idx_item)
            if item is None:
                if not GitHub.API_LIMIT_REACHED:
                    # show this warning only once
                    warnings.warn(self.API_LIMIT_MESSAGE)
                GitHub.API_LIMIT_REACHED = True
                # drop update date or another way to set that this issue was not fetch completely
                item = issues.get(idx, issues_new.get(idx))
                item["updated_at"] = None
            issues[idx] = item

        self.outdated = len(self.__update_issues_queue(issues, issues_new))
        return issues

    @staticmethod
    def __parse_user(field: dict) -> str:
        return field["user"]["login"]

    def __filer_commenter(self, comment: dict, in_period: bool) -> int:
        """Filter valid commenter by name and content."""
        if self._is_user_bot(self.__parse_user(comment)):
            return 1
        if in_period and not self._is_in_time_period(comment["updated_at"]):
            return 2
        if self._is_spam_message(comment["body"]):
            return 3
        return 0

    def _convert_to_simple(self, issues: list[dict]) -> list[dict]:
        """Aggregate issue/PR affiliations."""

        def _get_commenters(issue) -> list:
            return _unique_list(
                [
                    self.__parse_user(com)
                    for com in issue["comments"] + issue["review_comments"]
                    if self.__filer_commenter(com, in_period=True) == 0
                ]
            )

        # init collections of items from issues
        items = [
            {
                "type": "PR" if "pull" in issue["html_url"] else "issue",
                "state": issue["state"],
                "author": self.__parse_user(issue),
                "created_at": issue["created_at"],
                "closed_at": issue.get("closed_at"),
                "commenters": _get_commenters(issue),
            }
            for issue in tqdm(issues, desc="Parsing simplified tickets")
            # if fetch fails `comments` is int and `review_comments` is missing
            if isinstance(issue["comments"], list) and isinstance(issue.get("review_comments"), list)
        ]
        # update the counting time according item type
        [
            it.update(
                {
                    # use latest updated for issue and merged time for PRs
                    "count_at": it.get("updated_at", it["created_at"]) if it["type"] == "issue" else it["closed_at"]
                }
            )
            for it in tqdm(items, desc="Update simplified tickets")
        ]
        return items

    def _convert_comments_timeline(self, issues: list[dict]) -> list[dict]:
        """Aggregate comments for all issue/PR affiliations."""

        comments = []
        for item in tqdm(issues, desc="Parsing comments from all repo"):
            item_comments = item["comments"] if isinstance(item["comments"], list) else []
            item_comments += item.get("review_comments", [])
            if not isinstance(item_comments, list):
                continue
            comments += [
                {
                    "parent_type": "PR" if "pull" in item["html_url"] else "issue",
                    "parent_idx": int(item["number"]),
                    "author": self.__parse_user(cmt),
                    "created_at": cmt["created_at"],
                    "count_at": cmt.get("updated_at", cmt["created_at"]),
                }
                for cmt in item_comments
                if self.__filer_commenter(cmt, in_period=False) == 0
            ]
        # filter within given time frame
        return [cmt for cmt in comments if self._is_in_time_period(cmt["count_at"])]


def _unique_list(arr) -> list:
    return list(set(arr))


def _dt_update(arr, i):
    return pd.to_datetime(arr[i]["updated_at"])
