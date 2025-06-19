from github.Repository import Repository

class GitHubRepository(Repository):
    """
    Custom Repository class to add clone method.
    """
    def clone(self, overwrite: bool = False) -> None:
        """
        Clone the current repository.
        """
        pass