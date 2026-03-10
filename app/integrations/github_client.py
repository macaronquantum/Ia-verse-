from __future__ import annotations

from app.integrations.base import BaseClient


class GitHubClient(BaseClient):
    def create_issue(self, repo: str, title: str) -> dict:
        return {"repo": repo, "title": title, "issue_number": 1}

    def push(self, repo: str, branch: str) -> dict:
        return {"repo": repo, "branch": branch, "status": "simulated"}
