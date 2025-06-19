from pydantic import Field
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """
    Settings for GitHub Service.
    This class uses Pydantic to manage configuration settings, including
    environment variables and default values.
    """
    
    github_access_token: str = Field(
        default="",
        env="GITHUB_ACCESS_TOKEN"
    )
    
    """Access Token for GitHub API requests."""
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "allow"

settings = Settings()