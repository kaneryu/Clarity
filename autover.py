import sys
import subprocess
import re

commit_history = subprocess.check_output(['git', 'log', '--oneline']).decode('utf-8').split('\n')
commit_count = len(commit_history) - 1

typeincmap = [
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

mapmap = {item["type"]: index for index, item in enumerate(typeincmap)}

major = 0
minor = 0
patch = 0

regex = re.compile(r"(?P<hash>.*?) ?(?P<type>feat|chore|fix|perf|refactor|docs)(\((?P<scope>.*?)\))?: (?P<desc>.*)")

def getVer():
    global major, minor, patch
    for commit in commit_history:

        matches = regex.match(commit)
        if not matches:
            continue
        hash = matches.group("hash")
        type = matches.group("type")
        scope = matches.group("scope")
        desc = matches.group("desc")
        
        
        mitem = typeincmap[mapmap[type]]
        if mitem["inc"] == "major":
            major += mitem["amt"]
            minor = 0
            patch = 0
        if mitem["inc"] == "minor":
            minor += mitem["amt"]
            patch = 0
        if mitem["inc"] == "patch":
            patch += mitem["amt"]
        
        if "BREAKING CHANGE" in commit:
            major += 1

    return f"{major}.{minor}.{patch}"

def checkCommit(commit):
    matches = regex.match(commit)
    if not matches:
        return False
    return True
    