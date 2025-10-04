"""
Git post-commit hook for updating version files and changelog.
"""

import sys
import os
import logging
import subprocess

# Add the directory containing autover.py to the sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))
import autover
import autochangelog

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    # Prevent recursive execution
    if os.getenv("POST_COMMIT_RUNNING") == "1":
        return
    os.environ["POST_COMMIT_RUNNING"] = "1"
    
    try:
        # Get current version
        version = autover.getVer()
        logger.info(f"Calculated version: {version}")
        
        # Write version to files
        try:
            with open("./version.txt", "w", encoding="utf-8") as f:
                f.write(version)
            with open("./src/version.txt", "w", encoding="utf-8") as f:
                f.write(version)
        except IOError as e:
            logger.error(f"Failed to write version files: {e}")
            sys.exit(1)
        
        # Update run.py with version info
        try:
            with open("run.py", "r", encoding="utf-8") as f:
                lines = f.readlines()
            
            for i, line in enumerate(lines):
                if line.startswith("# nuitka-project: --product-version="):
                    lines[i] = f"# nuitka-project: --product-version={version}\n"
                if line.startswith("# nuitka-project: --file-version="):
                    lines[i] = f"# nuitka-project: --file-version={version}\n"
            
            with open("run.py", "w", encoding="utf-8") as f:
                f.writelines(lines)
        except IOError as e:
            logger.error(f"Failed to update run.py: {e}")
            sys.exit(1)
        
        # Update pyproject.toml with version info
        try:
            with open("pyproject.toml", "r", encoding="utf-8") as f:
                lines = f.readlines()
            
            for i, line in enumerate(lines):
                if line.startswith("version = "):
                    lines[i] = f'version = "{version}"\n'

            with open("pyproject.toml", "w", encoding="utf-8") as f:
                f.writelines(lines)
        except IOError as e:
            logger.error(f"Failed to update pyproject.toml: {e}")
            sys.exit(1)
        
        # Generate changelog
        try:
            autochangelog.write_changelog()
        except Exception as e:
            logger.error(f"Failed to generate changelog: {e}")
            sys.exit(1)
        
        # Stage all updated files and amend the commit
        try:
            subprocess.run(["git", "add", "version.txt"], check=True, timeout=5)
            subprocess.run(["git", "add", "src/version.txt"], check=True, timeout=5)
            subprocess.run(["git", "add", "CHANGELOG"], check=True, timeout=5)
            subprocess.run(["git", "add", "MOST_RECENT_CHANGELOG"], check=True, timeout=5)
            subprocess.run(["git", "add", "run.py"], check=True, timeout=5)
            subprocess.run(["git", "add", "pyproject.toml"], check=True, timeout=5)
            subprocess.run(["git", "commit", "--amend", "--no-edit"], check=True, timeout=10)
            logger.info("Successfully updated and amended commit")
        except subprocess.CalledProcessError as e:
            logger.error(f"Git command failed: {e}")
            sys.exit(1)
        except subprocess.TimeoutExpired:
            logger.error("Git command timed out")
            sys.exit(1)
    
    finally:
        # Clean up environment variable
        if "POST_COMMIT_RUNNING" in os.environ:
            del os.environ["POST_COMMIT_RUNNING"]


if __name__ == "__main__":
    main()