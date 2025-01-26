These are the commit hooks i use for conv commit checking, autoversioning and autochangelog.
Either
A:
copy all files in the folder into .git/hooks/
you have to do this upon any change to the files to keep them up to date

or

B:
create a commit hook that runs the files from the folder
It should look like this:

.git/hooks/commit-msg
```sh
#!/bin/sh
python ../../commit_hooks/commit-msg.py $1
```

.git/hooks/post-commit
```sh
#!/bin/sh
python ../../commit_hooks/post-commit.py
```
Then anytime you pull the repo, the command will run the latest version of the files.