# RepoRadar

What's trending on GitHub, and what it's built with.

Every day a GitHub Action takes the top 10 weekly and monthly repos from GitHub Trending, reads each new one (README, dependency files, file tree), asks Claude Code to explain the problem it solves, its stack by layer and what's new about it, and publishes the result as a page on GitHub Pages.

## How it works

| Step | File | What it does |
|---|---|---|
| 1 | `FetchTrending.py` | Downloads GitHub Trending (weekly and monthly) and saves the top 10 of each to `trending.json` |
| 2 | `FetchDetails.py` | For repos not analyzed yet, collects README, dependency files and file tree into `pending/` |
| 3 | Claude Code (in the workflow) | Reads each file in `pending/` and writes `analysis/<repo>.json` |
| 4 | `BuildPage.py` | Joins `trending.json` with `analysis/` and writes `docs/index.html` from `Template.html` |
| 5 | Workflow | Commits the results so GitHub Pages serves the new page |

Repos are analyzed only once. After the first run, only new repos cost anything.

## Setup

1. Create a public repo named `RepoRadar` and push these files.
2. On your computer run `claude setup-token` and copy the token.
3. In the repo: **Settings → Secrets and variables → Actions → New repository secret**. Name: `CLAUDE_CODE_OAUTH_TOKEN`, value: the token.
4. **Settings → Pages**: Source "Deploy from a branch", branch `main`, folder `/docs`.
5. **Actions → RepoRadar → Run workflow** to run it the first time. After that it runs every day at 12:00 UTC.

The page will be at `https://<your-user>.github.io/RepoRadar/`.
