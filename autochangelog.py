import sys
import subprocess
import re
subprocess.run(['git', 'init'])
commit_history = subprocess.check_output(['git', 'log', '--pretty=format:"%h %an %ad %s', '--date=short']).decode('utf-8').split('\n')
commit_history.reverse()
commit_count = len(commit_history) - 1

commit_type_increment_mapping = [
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

commit_type_index_map = {item["type"]: index for index, item in enumerate(commit_type_increment_mapping)}

major = 0
minor = 0
patch = 0

regex = re.compile(r"(?P<hash>\w+) (?P<author>\w+) (?P<date>\d{4}-\d{2}-\d{2})\s+(?P<type>feat|chore|fix|perf|refactor|docs)(\((?P<scope>.*?)\))?: (?P<desc>.*)")

def get_dict_changelog():
    global major, minor, patch
    changelog = {"0.1": []}
    for commit in commit_history:
        commit = commit.strip('"').strip(" ")
        print(f'"{commit}"')
        matches = regex.match(commit)
        if not matches:
            print(f"Skipping commit: {commit}")
            continue
        hash = matches.group("hash")
        type = matches.group("type")
        scope = matches.group("scope")
        desc = matches.group("desc")
        date = matches.group("date").strip(" ")
        author = matches.group("author").strip(" ")
        
        
        commit_increment_details = commit_type_increment_mapping[commit_type_index_map[type]]
        if commit_increment_details["inc"] == "major":
            major += commit_increment_details["amt"]
            minor = 0
            patch = 0
        if commit_increment_details["inc"] == "minor":
            minor += commit_increment_details["amt"]
            patch = 0
        if commit_increment_details["inc"] == "patch":
            patch += commit_increment_details["amt"]
        
        if "BREAKING CHANGE" in commit:
            major += 1
            
        if "BREAKING CHANGE" in commit or type == "major" or type == "feat":
            changelog[f"{major}.{minor}"] = [
                {
                    "type": type,
                    "hash": hash,
                    "scope": scope,
                    "desc": desc,
                    "date": date,
                    "author": author
                }
            ]
        else:
            changelog[f"{major}.{minor}"].append({
                "type": type,
                "hash": hash,
                "scope": scope,
                "desc": desc,
                "date": date,
                "author": author
            })

    return changelog

def checkCommit(commit):
    matches = regex.match(commit)
    if not matches:
        return False
    return True

def create_changelog():
    changelog = get_dict_changelog()
    changelog_str = ""
    most_recent_changelog = ""
    most_recent_version = list(changelog.keys())[-1]
    for version in reversed(changelog):
        new_features = ""
        bugfixes = ""
        perfimprovements = ""
        headline_changes = ""
        changelog_str += f"# Version {version}\n\n"
        if version == most_recent_version:
            most_recent_changelog = f"# Version {version}\n\n"
        
        headline_changes += "## Headline Changes\n\n"
        for item in changelog[version]:
            if item["type"] == "major":
                headline_changes += f"- {item['desc']} -- {item["author"]} on {item["date"]}\n"
        
        new_features += "## New Features\n\n"
        for item in changelog[version]:
            if item["type"] == "feat":
                new_features += f"- {item['desc']} -- {item["author"]} on {item["date"]}\n"
                
        bugfixes += "\n## Bugfixes\n\n"
        for item in changelog[version]:
            if item["type"] == "fix":
                bugfixes += f"- {item['desc']} -- {item["author"]} on {item["date"]}\n"
                
        perfimprovements += "\n## Performance Improvements\n\n"
        for item in changelog[version]:
            if item["type"] == "perf":
                perfimprovements += f"- {item['desc']} -- {item["author"]} on {item["date"]}\n"

        if headline_changes != "## Headline Changes\n\n":
            changelog_str += headline_changes
            if version == most_recent_version:
                most_recent_changelog += headline_changes
                
        if new_features != "## New Features\n\n":
            changelog_str += new_features
            if version == most_recent_version:
                most_recent_changelog += new_features
                
        if bugfixes != "\n## Bugfixes\n\n":
            changelog_str += bugfixes
            if version == most_recent_version:
                most_recent_changelog += bugfixes
                
        if perfimprovements != "\n## Performance Improvements\n\n":
            changelog_str += perfimprovements
            if version == most_recent_version:
                most_recent_changelog += perfimprovements
        
        changelog_str += "\n\n\n"
        
    return (changelog_str, most_recent_changelog)

def write_changelog():
    res = create_changelog()
    f = open("CHANGELOG", "w")
    fb = open("MOST_RECENT_CHANGELOG", "w")
    
    f.write(res[0])
    fb.write(res[1])
    
    fb.close()
    f.close()
