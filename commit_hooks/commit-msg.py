import sys
import os

import semantic_release.version as semver
import semantic_release.commit_parser.conventional as convparser
import git.objects.commit as gitcommit


def main():
    msg = open(sys.argv[1]).read()

    if not msg.startswith("Merge"):
        parser = convparser.ConventionalCommitParser()
        valid = parser.parse_message(msg) is not None
        if not valid:
            print(f"Commit message '{msg}' is not valid.")
            sys.exit(1)


main()
