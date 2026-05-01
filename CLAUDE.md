\# CLAUDE.md



Guidance for Claude Code agent when working on this repository.



\## Git commit conventions



CRITICAL: All commits in this repository must reflect Kenny Ramadhan as sole author. Specifically:



1\. NEVER add Co-Authored-By footer mentioning Claude or anthropic.com to commit messages

2\. NEVER add "Generated with Claude Code" or any AI attribution lines

3\. NEVER override the local git config user.name or user.email

4\. NEVER include any AI attribution, signature, or footer in commit messages

5\. Commit messages follow conventional commits style (feat, fix, docs, refactor, chore, test) without AI attribution



The commit history is a public artifact of Kenny Ramadhan's QA engineering work. AI assistance is welcome and effective in development, but commit attribution stays human-only by design.



A commit-msg git hook is installed locally that will REJECT commits with AI attribution. Don't try to bypass it.



\## Repository purpose



This is a public QA automation portfolio showcasing production-grade test architecture using Practice Software Testing demo app.



Stack:

\- Python 3.12+

\- Playwright async API

\- pytest + pytest-asyncio

\- Allure reporting

\- uv package manager



\## Architectural rules



Refer to ARCHITECTURE.md for design decisions, ALLURE\_TEST\_IDS.md for test naming convention.



Key non-negotiables:

\- All test functions are async

\- Page Object Model strict (no selectors in tests)

\- BaseService pattern for API clients

\- Pydantic models for API responses

\- Allure decorators @allure.id and @allure.title mandatory on every test

\- Type hints on all public functions, mypy strict mode



\## Demo target



Practice Software Testing (Toolshop):

\- Web UI: practicesoftwaretesting.com

\- REST API: api.practicesoftwaretesting.com



Do not target other apps unless explicitly instructed.

