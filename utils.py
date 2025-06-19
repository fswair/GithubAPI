# coding: utf-8

"""
GitHub Service Module
This module provides functionality to interact with GitHub repositories.
"""

from models.users import User
from models.repos import GitHubRepository

from github import Github
from github.ContentFile import ContentFile
from github.GithubObject import NotSet, Opt

from pathlib import Path
from typing import Iterable
from base64 import b64decode
from functools import partial
from collections import defaultdict


def decode_content(content: str) -> tuple[str, int]:
    """
    Decodes base64-encoded content.

    Args:
        content (str): Base64 encoded content.

    Returns:
        tuple[str, int]: Decoded content and a flag indicating if it was decoded as UTF-8 (1) or binary (0).
    """
    try:
        return b64decode(content).decode('utf-8'), 1
    except Exception:
        return b64decode(content), 0


def limiter(data: Iterable, limit: int | None = None) -> Iterable:
    """
    Limits the number of items in an iterable.

    Args:
        data (Iterable): The data to limit.
        limit (int | None): The maximum number of items to return. If None, returns all items.

    Returns:
        Iterable: The limited data.
    """
    if limit is None:
        return data
    return data[:limit] if isinstance(data, list) else data


class GitHub(Github):
    def __init__(self, token: str, warnings: bool = True, **kwargs):
        """
        Initializes the GitHub client.

        Args:
            token (str): GitHub API token.
            **kwargs: Additional arguments for the GitHub client.
        """
        self.info = lambda *args, **kwargs: None if not warnings else print(*args, **kwargs)
        super().__init__(login_or_token=token, **kwargs)

    def get_repo_content(self, repo_name: str, path: str = "", ref: Opt[str] = NotSet) -> list[ContentFile]:
        """
        Retrieves the contents of a repository.

        Args:
            repo_name (str): Full name of the repository (e.g., "owner/repo").
            path (str, optional): Path within the repository. Defaults to "".

        Returns:
            list[ContentFile]: List of repository contents.
        """
        repo = self.get_repo(repo_name)
        return repo.get_contents(path, ref=ref)

    def get_file_content(self, repo_name: str, file_path: str, ref: Opt[str] = NotSet) -> tuple[str, int]:
        """
        Retrieves the content of a file in a repository.

        Args:
            repo_name (str): Full name of the repository (e.g., "owner/repo").
            file_path (str): Path to the file within the repository.
            ref (Opt[str], optional): Git reference (branch, tag, or commit). Defaults to NotSet.

        Returns:
            tuple[str, int]: Decoded file content and a flag indicating its type.
        """
        repo = self.get_repo(repo_name)
        file_content = repo.get_contents(file_path, ref=ref)
        return decode_content(file_content.content or b'')

    def get_repo(self, repo_full_name: str) -> GitHubRepository:
        """
        Retrieves a repository by its full name.

        Args:
            repo_full_name (str): Full name of the repository (e.g., "owner/repo").

        Returns:
            GitHubRepository: The repository object.
        """
        repo = super().get_repo(repo_full_name)
        repo.clone = partial(self.clone_repo, repo_origin=repo.full_name)
        return repo

    def get_repo_branches(self, repo_name: str) -> list[str]:
        """
        Retrieves the branches of a repository.

        Args:
            repo_name (str): Full name of the repository (e.g., "owner/repo").

        Returns:
            list[str]: List of branch names.
        """
        repo = self.get_repo(repo_name)
        return [branch.name for branch in repo.get_branches()]

    def get_user_repo(self, username: str = None, repo_name: str = None, repo_origin: str = None) -> GitHubRepository:
        """
        Retrieves a specific repository of a user.

        Args:
            username (str, optional): GitHub username. Defaults to None.
            repo_name (str, optional): Repository name. Defaults to None.
            repo_origin (str, optional): Full repository name (e.g., "owner/repo"). Defaults to None.

        Returns:
            GitHubRepository: The repository object.
        """
        if not repo_origin:
            repo_origin = f"{username}/{repo_name}"
        return self.get_repo(repo_origin)

    def get_user_repos(self, username: str, limit: int | None = None) -> list[GitHubRepository]:
        """
        Retrieves repositories of a user.

        Args:
            username (str): GitHub username.
            limit (int | None, optional): Maximum number of repositories to return. Defaults to None.

        Returns:
            list[GitHubRepository]: List of repositories.
        """
        user = self.get_user(username)
        repos = list(user.get_repos(type="sources", direction="desc", sort="updated"))
        for repo in repos:
            repo.clone = partial(self.clone_repo, repo_origin=repo.full_name)
        return limiter(repos, limit)

    def get_user_info(self, username: str, limit: int | None = None) -> User:
        """
        Retrieves detailed information about a user.

        Args:
            username (str): GitHub username.
            limit (int | None, optional): Maximum number of items to return for gists and repositories. Defaults to None.

        Returns:
            User: User object containing detailed information.
        """
        user = self.get_user(username)
        gists = list(user.get_gists(user.created_at))
        repos = list(user.get_repos(type="sources", direction="desc", sort="updated"))
        user_repo_issues = defaultdict(list)
        user_repo_pull_requests = defaultdict(list)

        for repo in repos:
            user_repo_issues[repo.name] = repo.get_issues(state="all")
            user_repo_pull_requests[repo.name] = repo.get_pulls(state="all")

        return User(
            id=user.id,
            user=user,
            gists=limiter(gists, limit),
            repos=limiter(repos, limit),
            followings=[],  # Placeholder for following list
            followers=[],  # Placeholder for followers list
            user_repo_issues=user_repo_issues,
            user_repo_pull_requests=user_repo_pull_requests
        )

    def clone_repo(self, username: str = None, repo_name: str = None, repo_origin: str = None, ref: Opt[str] = NotSet, overwrite: bool = False) -> None:
        """
        Clones a repository locally.

        Args:
            username (str, optional): GitHub username. Defaults to None.
            repo_name (str, optional): Repository name. Defaults to None.
            repo_origin (str, optional): Full repository name (e.g., "owner/repo"). Defaults to None.

        Returns:
            None
        """
        if not repo_origin:
            repo_origin = f"{username}/{repo_name}"
        else:
            username, repo_name = repo_origin.split('/')
        repo = self.get_repo(repo_origin)
        contents = repo.get_contents("", ref=ref)

        def process_content(content: ContentFile) -> None:
            """
            Recursively processes repository contents.

            Args:
                content (ContentFile): Content file object.

            Returns:
                None
            """
            if content.type == "dir":
                self.info(f"Processing directory: {content.path}")
                dir_path = Path(repo_name) / content.path
                dir_path.mkdir(parents=True, exist_ok=True)
                sub_contents = self.get_repo_content(repo_origin, content.path)
                for sub_content in sub_contents:
                    process_content(sub_content)
            elif content.type == "file":
                self.info(f"Processing file: {content.path}")
                file_content, flag = self.get_file_content(repo_origin, content.path)
                file_path = Path(repo_name) / content.path
                mode = 'w' if flag else 'wb'
                with file_path.open(mode, encoding='utf-8' if flag else None) as f:
                    f.write(file_content)

        repo_path = Path(repo_name)
        if repo_path.exists():
            if not overwrite:
                self.info(f"Repository {repo_name} already exists. Skipping clone. (Set overwrite=True to force clone)")
                return
            else:
                self.info(f"Repository {repo_name} already exists. Overwriting objects.")
        repo_path.mkdir(parents=True, exist_ok=True)
        self.info(f"Processing repository: {repo_name}")
        for content in contents:
            process_content(content)