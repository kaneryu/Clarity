"""
Git commit-msg hook for validating conventional commit format.
"""

import sys
import os
import logging

# Add the directory containing autover.py to the sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))
import autover

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    if len(sys.argv) < 2:
        logger.error("Usage: commit-msg.py <commit-msg-file>")
        sys.exit(1)
    
    try:
        with open(sys.argv[1], "r", encoding="utf-8") as f:
            msg = f.read()
    except IOError as e:
        logger.error(f"Failed to read commit message file: {e}")
        sys.exit(1)
    
    if not msg.startswith("Merge"):
        valid = autover.checkCommit(msg)
        if not valid:
            logger.error(f"Commit message does not follow conventional commit format.")
            logger.error(f"Expected format: type(scope): description")
            logger.error(f"Valid types: feat, fix, perf, refactor, chore, docs")
            logger.error(f"Your message: {msg}")
            sys.exit(1)
        
        try:
            version = autover.getVer()
            with open("./version.txt", "w", encoding="utf-8") as f:
                f.write(version)
            with open("./src/version.txt", "w", encoding="utf-8") as f:
                f.write(version)
            logger.info(f"Version updated to: {version}")
        except IOError as e:
            logger.error(f"Failed to write version files: {e}")
            sys.exit(1)


if __name__ == "__main__":
    main()