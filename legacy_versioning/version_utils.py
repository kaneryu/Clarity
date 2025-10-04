"""
Shared utilities for automatic versioning and changelog generation.
Implements conventional commit parsing and semantic versioning logic.
"""

import re
import subprocess
import logging
from typing import Dict, List, Optional, Tuple

# Set up logging
logger = logging.getLogger(__name__)

# Commit type to version increment mapping
COMMIT_TYPE_INCREMENT_MAPPING = [
    {
        "type": "feat",
        "inc": "minor",
        "amt": 1
    },
    {
        "type": "fix",
        "inc": "patch",
        "amt": 1
    },
    {
        "type": "perf",
        "inc": "patch",
        "amt": 1
    },
    {
        "type": "refactor",
        "inc": "patch",
        "amt": 1
    },
    {
        "type": "chore",
        "inc": "patch",
        "amt": 0
    },
    {
        "type": "docs",
        "inc": "patch",
        "amt": 0
    }
]

COMMIT_TYPE_INDEX_MAP = {item["type"]: index for index, item in enumerate(COMMIT_TYPE_INCREMENT_MAPPING)}

# Regex for parsing conventional commits (simple format - for git log)
SIMPLE_COMMIT_REGEX = re.compile(
    r"(?P<hash>\S+)\s+(?P<type>feat|chore|fix|perf|refactor|docs)"
    r"(?:\((?P<scope>[^)]*)\))?:\s+(?P<desc>.*)"
)

# Regex for validating commit messages (without hash prefix)
COMMIT_MESSAGE_REGEX = re.compile(
    r"(?P<type>feat|chore|fix|perf|refactor|docs)"
    r"(?:\((?P<scope>[^)]*)\))?:\s+(?P<desc>.*)"
)

# Regex for parsing conventional commits (detailed format with author and date)
DETAILED_COMMIT_REGEX = re.compile(
    r"(?P<hash>\S+)\s+(?P<author>.+?)\s+(?P<date>\d{4}-\d{2}-\d{2})\s+"
    r"(?P<type>feat|chore|fix|perf|refactor|docs)"
    r"(?:\((?P<scope>[^)]*)\))?:\s+(?P<desc>.*)"
)


def is_git_repository() -> bool:
    """Check if current directory is a git repository."""
    try:
        subprocess.run(
            ['git', 'rev-parse', '--git-dir'],
            check=True,
            capture_output=True,
            timeout=5
        )
        return True
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError):
        return False


def is_breaking_change(commit_message: str) -> bool:
    """Check if commit message indicates a breaking change."""
    return "BREAKING CHANGE" in commit_message or "BUMP MAJOR" in commit_message


def get_commit_history_simple() -> List[str]:
    """
    Get git commit history in simple format (hash + message).
    Returns commits in chronological order (oldest first).
    """
    try:
        output = subprocess.check_output(
            ['git', 'log', '--oneline'],
            timeout=30,
            encoding='utf-8'
        )
        commits = output.strip().split('\n')
        commits.reverse()  # Oldest first
        return commits
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError) as e:
        logger.error(f"Failed to get git commit history: {e}")
        return []


def get_commit_history_detailed() -> List[str]:
    """
    Get git commit history with author and date.
    Returns commits in chronological order (oldest first).
    """
    try:
        output = subprocess.check_output(
            ['git', 'log', '--pretty=format:%h %an %ad %s', '--date=short'],
            timeout=30,
            encoding='utf-8'
        )
        commits = output.strip().split('\n')
        commits.reverse()  # Oldest first
        return commits
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError) as e:
        logger.error(f"Failed to get git commit history: {e}")
        return []


def parse_simple_commit(commit: str) -> Optional[Dict[str, str]]:
    """
    Parse a commit in simple format (hash + message).
    Returns dict with keys: hash, type, scope, desc, or None if invalid.
    """
    commit = commit.strip()
    if not commit or commit.startswith("Merge"):
        return None
    
    matches = SIMPLE_COMMIT_REGEX.match(commit)
    if not matches:
        logger.debug(f"Skipping invalid commit format: {commit}")
        return None
    
    return {
        "hash": matches.group("hash"),
        "type": matches.group("type"),
        "scope": matches.group("scope") or "",
        "desc": matches.group("desc"),
        "full_message": commit
    }


def parse_detailed_commit(commit: str) -> Optional[Dict[str, str]]:
    """
    Parse a commit in detailed format (hash, author, date, message).
    Returns dict with keys: hash, author, date, type, scope, desc, or None if invalid.
    """
    commit = commit.strip()
    if not commit or commit.startswith("Merge"):
        return None
    
    matches = DETAILED_COMMIT_REGEX.match(commit)
    if not matches:
        logger.debug(f"Skipping invalid commit format: {commit}")
        return None
    
    return {
        "hash": matches.group("hash"),
        "author": matches.group("author").strip(),
        "date": matches.group("date").strip(),
        "type": matches.group("type"),
        "scope": matches.group("scope") or "",
        "desc": matches.group("desc"),
        "full_message": commit
    }


def calculate_version_from_commits(commits: List[str], use_detailed: bool = False) -> Tuple[int, int, int]:
    """
    Calculate semantic version from commit history.
    Returns tuple of (major, minor, patch).
    """
    major = 0
    minor = 0
    patch = 0
    
    parse_func = parse_detailed_commit if use_detailed else parse_simple_commit
    
    for commit in commits:
        parsed = parse_func(commit)
        if not parsed:
            continue
        
        commit_type = parsed["type"]
        full_message = parsed.get("full_message", commit)
        
        # Get increment details for this commit type
        if commit_type not in COMMIT_TYPE_INDEX_MAP:
            logger.warning(f"Unknown commit type: {commit_type}")
            continue
        
        commit_increment = COMMIT_TYPE_INCREMENT_MAPPING[COMMIT_TYPE_INDEX_MAP[commit_type]]
        
        # Check for breaking changes first (takes precedence)
        if is_breaking_change(full_message):
            major += 1
            minor = 0
            patch = 0
        # Apply normal increment
        elif commit_increment["inc"] == "major":
            major += commit_increment["amt"]
            minor = 0
            patch = 0
        elif commit_increment["inc"] == "minor":
            minor += commit_increment["amt"]
            patch = 0
        elif commit_increment["inc"] == "patch":
            patch += commit_increment["amt"]
    
    return (major, minor, patch)


def check_commit_format(commit_message: str) -> bool:
    """
    Validate if a commit message follows conventional commit format.
    Returns True if valid, False otherwise.
    """
    if commit_message.startswith("Merge"):
        return True  # Merge commits are allowed
    
    # For commit messages (without hash), use COMMIT_MESSAGE_REGEX
    return COMMIT_MESSAGE_REGEX.match(commit_message.strip()) is not None


def get_version_string() -> str:
    """
    Get the current semantic version as a string.
    Returns version in format: major.minor.patch
    """
    commits = get_commit_history_simple()
    major, minor, patch = calculate_version_from_commits(commits)
    return f"{major}.{minor}.{patch}"
