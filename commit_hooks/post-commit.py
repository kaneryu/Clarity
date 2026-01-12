import sys
import os


import subprocess
import git
import semantic_release
import semantic_release.version.algorithm as semverAlgorithm
import semantic_release.changelog as semverChangelog
import semantic_release.commit_parser.conventional as convparser

from semantic_release.changelog.context import ChangelogContext
from semantic_release.changelog.context import (
    ReleaseNotesContext,
    autofit_text_width,
    create_pypi_url,
    make_changelog_context,
)
from semantic_release.changelog.template import environment, recursive_render
from semantic_release.changelog.context import ChangelogMode
from semantic_release.changelog.release_history import Release, ReleaseHistory
from semantic_release.cli.config import RuntimeContext, ChangelogOutputFormat
from semantic_release.hvcs.github import Github

import semantic_release.cli.changelog_writer as semverChangelogWriter

from legacy_versioning import autover, autochangelog

changelogPath = os.path.join(os.getcwd(), "CHANGELOG.md")
mostRecentChangelogPath = os.path.join(os.getcwd(), "MOST_RECENT_CHANGELOG.md")


def getChangelog(mode: ChangelogMode = ChangelogMode.INIT) -> str:
    # write_default_changelog -> render_default_changelog_file -> changelog text
    repo = git.Repo(os.getcwd())
    remote = next(iter(repo.remotes), None)
    rh = ReleaseHistory.from_git_history(
        repo=repo,
        translator=semantic_release.VersionTranslator(),
        commit_parser=convparser.ConventionalCommitParser(),
        exclude_commit_patterns=[],
    )
    hvcs = Github(remote_url=remote.url if remote else None)
    changelog_context = make_changelog_context(
        hvcs_client=hvcs,
        release_history=rh,
        mode=mode,
        prev_changelog_file=changelogPath,
        insertion_flag="<!-- changelog -->",
        mask_initial_release=False,
    )
    changelog_text = semverChangelogWriter.render_default_changelog_file(
        output_format=ChangelogOutputFormat.MARKDOWN,
        changelog_context=changelog_context,
        changelog_style="conventional",
    )
    return changelog_text


def getVersion():
    repo = git.Repo(os.getcwd())
    translator = semantic_release.VersionTranslator()
    parser = convparser.ConventionalCommitParser()
    return semverAlgorithm.next_version(
        repo=repo,
        translator=translator,
        commit_parser=parser,
        allow_zero_version=True,
        major_on_zero=False,
        prerelease=False,
    )


def main():
    if os.getenv("POST_COMMIT_RUNNING") == "1":
        return
    os.environ["POST_COMMIT_RUNNING"] = "1"

    version = autover.getVer()
    print(f"Calculated version: {version}")
    open("./version.txt", "w").write(version)
    open("./src/version.txt", "w").write(version)

    with open("run.py", "r") as f:
        lines = f.readlines()

    for i, line in enumerate(lines):
        if line.startswith("# nuitka-project: --product-version="):
            lines[i] = f"# nuitka-project: --product-version={version}\n"
        if line.startswith("# nuitka-project: --file-version="):
            lines[i] = f"# nuitka-project: --file-version={version}\n"
        if line.startswith("# nuitka-project: --file-description="):
            lines[i] = f'# nuitka-project: --file-description="Clarity v{version}"\n'

    with open("run.py", "w") as f:
        f.writelines(lines)

    with open("pyproject.toml", "r") as f:
        lines = f.readlines()

    for i, line in enumerate(lines):
        if line.startswith("version = "):
            lines[i] = f'version = "{version}"\n'

    with open("pyproject.toml", "w") as f:
        f.writelines(lines)

    changelogs = autochangelog.create_changelog()
    fullChangelog = changelogs[0]
    mostRecentChangelog = changelogs[1]

    with open(changelogPath, "w", encoding="utf-8") as f:
        f.write(fullChangelog)

    with open(mostRecentChangelogPath, "w", encoding="utf-8") as f:
        f.write(mostRecentChangelog)

    # subprocess.run(["git", "init"], check=True)
    # subprocess.run(["git", "add", "version.txt"], check=True)
    # subprocess.run(["git", "add", "src/version.txt"], check=True)
    # subprocess.run(["git", "add", "CHANGELOG.md"], check=True)
    # subprocess.run(["git", "add", "MOST_RECENT_CHANGELOG.md"], check=True)
    # subprocess.run(["git", "add", "run.py"], check=True)
    # subprocess.run(["git", "add", "pyproject.toml"], check=True)
    # subprocess.run(["git", "commit", "--amend", "--no-edit"], check=True)

    os.environ["POST_COMMIT_RUNNING"] = "0"


main()
