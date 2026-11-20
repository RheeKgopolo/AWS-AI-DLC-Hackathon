# Git workflow

- You MUST NEVER commit to `main`. Work happens on a branch; a person merges.
- Branch names MUST be `<type>/<slug>`: type is one of `feat`, `fix`, `chore`, `docs`, `refactor`; slug is lowercase kebab-case, 3 to 5 words (e.g. `feat/explain-empty-invite-list`).
- Commit messages MUST follow Conventional Commits: `<type>(<scope>): <imperative summary>`, summary 72 characters or fewer, no trailing period (e.g. `fix(app): explain why no spend request was drafted`).
- You MUST make one commit per task in `tasks.md`, and only after that task's test passes (`.venv/bin/pytest`).
- You MUST NEVER run `git push`, `git merge`, `git rebase`, `git reset --hard`, `git branch -D`, or check out `main`.
- You MUST NEVER stage `.env*`, `.venv/`, `test-results/`, `.playwright-mcp/`, or any credential.
- You MUST NEVER add a dependency without the user's approval in the current conversation.
- Before starting a branch, you MUST check `git status`. If there is uncommitted work, stop and ask the user what to do with it.
- At the end of a branch, you MUST report: branch name, commits (`git log --oneline main..`), tests run and results, and any deviation from the spec.
