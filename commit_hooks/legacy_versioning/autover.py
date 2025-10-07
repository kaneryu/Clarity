"""
Automatic versioning based on conventional commits.
This module provides functions for calculating semantic versions from git history
and validating commit message formats.
"""

import logging
from .version_utils import (
    get_version_string,
    check_commit_format,
    is_git_repository
)

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def getVer() -> str:
    """
    Calculate the current semantic version from git commit history.
    Returns version string in format: major.minor.patch
    """
    if not is_git_repository():
        logger.error("Not in a git repository")
        return "0.0.0"
    
    try:
        return get_version_string()
    except Exception as e:
        logger.error(f"Failed to calculate version: {e}")
        return "0.0.0"


def checkCommit(commit: str) -> bool:
    """
    Validate if a commit message follows conventional commit format.
    Returns True if valid, False otherwise.
    """
    try:
        return check_commit_format(commit)
    except Exception as e:
        logger.error(f"Failed to validate commit: {e}")
        return False