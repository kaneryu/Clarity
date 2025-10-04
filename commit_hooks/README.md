# Git Hooks - Legacy Mode

The git hooks in this directory (`commit-msg.py` and `post-commit.py`) are now **optional** since python-semantic-release handles versioning automatically in CI/CD.

## Options

### Option 1: Keep Hooks for Local Validation (Recommended for transition)

Keep the hooks active for local commit message validation. They will still validate conventional commit format.

To use the legacy versioning functions, update the imports to point to `legacy_versioning/`:

```python
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../legacy_versioning')))
```

### Option 2: Disable Hooks

If you want to fully rely on python-semantic-release, you can disable the hooks:

```bash
# Remove hook path from git config
git config --unset core.hooksPath

# Or rename them to disable
mv commit_hooks/commit-msg.py commit_hooks/commit-msg.py.disabled
mv commit_hooks/post-commit.py commit_hooks/post-commit.py.disabled
```

### Option 3: Use PSR for Validation

Use python-semantic-release to validate commits before pushing:

```bash
# Add to your workflow
semantic-release --noop version
```

This will show you what the next version would be based on your commits.

## Current Status

The hooks are still in place but reference old scripts. Choose one of the options above based on your preference.

## Recommendation

For a personal project, **Option 2 (disable hooks)** is simplest. Let PSR handle everything in CI/CD, and if you make a bad commit message, PSR will just skip the release (no harm done).
