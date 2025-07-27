import sys
import os
# Add the directory containing autover.py to the sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))
import autover
import autochangelog
import subprocess
def main():
    if os.getenv("POST_COMMIT_RUNNING") == "1":
        return
    os.environ["POST_COMMIT_RUNNING"] = "1"
    
    version = autover.getVer()
    open("./version.txt", "w").write(version)
    open("./src/version.txt", "w").write(version)
    
    with open("run.py", "r") as f:
        lines = f.readlines()
    
    for i, line in enumerate(lines):
        if line.startswith("# nuitka-project: --product-version="):
            lines[i] = f"# nuitka-project: --product-version={version}\n"
        if line.startswith("# nuitka-project: --file-version="):
            lines[i] = f"# nuitka-project: --file-version={version}\n"
    
    with open("run.py", "w") as f:
        f.writelines(lines)
        
    
    with open("pyproject.toml", "r") as f:
        lines = f.readlines()
    
    for i, line in enumerate(lines):
        if line.startswith("version = "):
            lines[i] = f'version = "{version}"\n'

    with open("pyproject.toml", "w") as f:
        f.writelines(lines)
    
    autochangelog.write_changelog()
    
    subprocess.run(["git", "init"], check=True)
    subprocess.run(["git", "add", "version.txt"], check=True)
    subprocess.run(["git", "add", "src/version.txt"], check=True)
    subprocess.run(["git", "add", "CHANGELOG"], check=True)
    subprocess.run(["git", "add", "MOST_RECENT_CHANGELOG"], check=True)
    subprocess.run(["git", "add", "run.py"], check=True)
    subprocess.run(["git", "add", "pyproject.toml"], check=True)
    subprocess.run(["git", "commit", "--amend", "--no-edit"], check=True)
    
    os.environ["POST_COMMIT_RUNNING"] = "0"

main()