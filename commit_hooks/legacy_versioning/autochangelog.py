"""
Automatic changelog generation based on conventional commits.
Generates both full changelog and most recent changelog for CI/CD.
"""

import logging
from typing import Dict, List, Tuple
from version_utils import (
    get_commit_history_detailed,
    parse_detailed_commit,
    is_git_repository,
    is_breaking_change,
    COMMIT_TYPE_INCREMENT_MAPPING,
    COMMIT_TYPE_INDEX_MAP,
)

# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def get_dict_changelog() -> Dict[str, List[Dict[str, str]]]:
    """
    Parse git commit history and organize into changelog dictionary.
    Returns dict with version strings as keys and list of commits as values.
    """
    if not is_git_repository():
        logger.error("Not in a git repository")
        return {"0.1.0": []}

    commit_history = get_commit_history_detailed()

    major = 0
    minor = 0
    patch = 0

    changelog: Dict[str, List[Dict[str, str]]] = {}
    current_version = f"{major}.{minor}.{patch}"
    changelog[current_version] = []

    for commit in commit_history:
        parsed = parse_detailed_commit(commit)
        if not parsed:
            continue

        commit_hash = parsed["hash"]
        commit_type = parsed["type"]
        scope = parsed["scope"]
        desc = parsed["desc"]
        date = parsed["date"]
        author = parsed["author"]
        full_message = parsed["full_message"]

        # Calculate version increment
        if commit_type not in COMMIT_TYPE_INDEX_MAP:
            logger.warning(f"Unknown commit type: {commit_type}")
            continue

        commit_increment_details = COMMIT_TYPE_INCREMENT_MAPPING[
            COMMIT_TYPE_INDEX_MAP[commit_type]
        ]

        # Check for breaking changes first (takes precedence)
        if is_breaking_change(full_message):
            major += 1
            minor = 0
            patch = 0
            current_version = f"{major}.{minor}.{patch}"
            changelog[current_version] = []
        # Apply normal increment
        elif commit_increment_details["inc"] == "major":
            major += commit_increment_details["amt"]
            minor = 0
            patch = 0
            if commit_increment_details["amt"] > 0:
                current_version = f"{major}.{minor}.{patch}"
                changelog[current_version] = []
        elif commit_increment_details["inc"] == "minor":
            minor += commit_increment_details["amt"]
            patch = 0
            if commit_increment_details["amt"] > 0:
                current_version = f"{major}.{minor}.{patch}"
                if current_version not in changelog:
                    changelog[current_version] = []
        elif commit_increment_details["inc"] == "patch":
            patch += commit_increment_details["amt"]
            if commit_increment_details["amt"] > 0:
                current_version = f"{major}.{minor}.{patch}"
                if current_version not in changelog:
                    changelog[current_version] = []

        # Append commit to current version (FIXED: no longer overwrites)
        changelog[current_version].append(
            {
                "type": commit_type,
                "hash": commit_hash,
                "scope": scope,
                "desc": desc,
                "date": date,
                "author": author,
            }
        )

    return changelog


def create_changelog() -> Tuple[str, str]:
    """
    Create formatted changelog strings.
    Returns tuple of (full_changelog, most_recent_changelog).
    """
    changelog = get_dict_changelog()
    changelog_str = ""
    most_recent_changelog = ""

    if not changelog:
        logger.warning("No changelog entries found")
        return ("", "")

    most_recent_version = list(changelog.keys())[-1]

    for version in reversed(changelog.keys()):
        version_section = f"# Version {version}\n\n"
        headline_changes = ""
        new_features = ""
        bugfixes = ""
        perfimprovements = ""

        # Headline Changes (Breaking changes - using is_breaking_change logic)
        headline_items = [
            item
            for item in changelog[version]
            if item.get("desc")
            and (
                "BREAKING CHANGE" in item.get("desc", "")
                or "BUMP MAJOR" in item.get("desc", "")
            )
        ]
        if headline_items:
            headline_changes = "## Headline Changes\n\n"
            for item in headline_items:
                headline_changes += (
                    f"- {item['desc']} -- {item['author']} on {item['date']}\n"
                )
            headline_changes += "\n"

        # New Features
        feature_items = [item for item in changelog[version] if item["type"] == "feat"]
        if feature_items:
            new_features = "## New Features\n\n"
            for item in feature_items:
                new_features += (
                    f"- {item['desc']} -- {item['author']} on {item['date']}\n"
                )
            new_features += "\n"

        # Bugfixes
        bugfix_items = [item for item in changelog[version] if item["type"] == "fix"]
        if bugfix_items:
            bugfixes = "## Bugfixes\n\n"
            for item in bugfix_items:
                bugfixes += f"- {item['desc']} -- {item['author']} on {item['date']}\n"
            bugfixes += "\n"

        # Performance Improvements
        perf_items = [item for item in changelog[version] if item["type"] == "perf"]
        if perf_items:
            perfimprovements = "## Performance Improvements\n\n"
            for item in perf_items:
                perfimprovements += (
                    f"- {item['desc']} -- {item['author']} on {item['date']}\n"
                )
            perfimprovements += "\n"

        # Assemble version section
        version_content = (
            version_section
            + headline_changes
            + new_features
            + bugfixes
            + perfimprovements
        )
        changelog_str += version_content + "\n"

        # Save most recent version
        if version == most_recent_version:
            most_recent_changelog = version_content

    return (changelog_str, most_recent_changelog)


def write_changelog() -> None:
    """
    Generate and write changelog files to disk.
    Creates CHANGELOG and MOST_RECENT_CHANGELOG files.
    """
    try:
        changelog_full, changelog_recent = create_changelog()

        # Write full changelog
        with open("CHANGELOG", "w", encoding="utf-8") as f:
            f.write(changelog_full)
        logger.info("Successfully wrote CHANGELOG")

        # Write most recent changelog
        with open("MOST_RECENT_CHANGELOG", "w", encoding="utf-8") as f:
            f.write(changelog_recent)
        logger.info("Successfully wrote MOST_RECENT_CHANGELOG")

    except IOError as e:
        logger.error(f"Failed to write changelog files: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error while generating changelog: {e}")
        raise
