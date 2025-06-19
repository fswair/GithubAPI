from collections import defaultdict
from pydantic import BaseModel, Field
from typing import List, Optional
from github.AuthenticatedUser import AuthenticatedUser
from github.NamedUser import NamedUser
from github.Gist import Gist
from github.Issue import Issue
from github.PullRequest import PullRequest
from github.Repository import Repository

class User(BaseModel):
    """
    Represents a user in the GitHub system.
    """
    id: Optional[int] = Field(
        default=None,
        description="Unique identifier for the user."
    )
    
    user: Optional[AuthenticatedUser | NamedUser] = Field(
        default=None,
        description="The authenticated user or named user object from GitHub API."
    )
    
    gists: Optional[List[Gist]] = Field(
        default=[],
        description="Number of gists created by the user."
    )
    
    repos: Optional[List[Repository]] = Field(
        default=[],
        description="List of repositories owned by the user."
    )
    
    followings: Optional[List[NamedUser]] = Field(
        default=[],
        description="List of users that this user is following."
    )
    
    followers: Optional[List[NamedUser]] = Field(
        default=[],
        description="List of users that are following this user."
    )
    
    user_repo_issues: Optional[defaultdict[str, List[Issue]]] = Field(
        default={},
        description="Dictionary mapping repository names to lists of issues created by the user."
    )
    
    user_repo_pull_requests: Optional[defaultdict[str, List[PullRequest]]] = Field(
        default={},
        description="Dictionary mapping repository names to lists of pull requests created by the user."
    )
    
    model_config = {
        "arbitrary_types_allowed": True,
        "extra": "allow"
    }