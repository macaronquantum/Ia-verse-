from __future__ import annotations

from base64 import b64encode
from dataclasses import dataclass, field
from typing import Dict

from app.config import settings


@dataclass
class AccountSession:
    site: str
    username: str
    encrypted_secret: str
    logged_in: bool = False
    audit: list[str] = field(default_factory=list)


class AccountManager:
    def __init__(self) -> None:
        self.sessions: Dict[str, AccountSession] = {}

    def _check_policy(self, site: str) -> None:
        if "forbidden" in site:
            raise ValueError("automation policy violation")

    def create_account(self, site: str, profile_spec: Dict) -> AccountSession:
        self._check_policy(site)
        username = profile_spec.get("username", "dev-user")
        secret = b64encode(profile_spec.get("password", "pass").encode()).decode()
        session = AccountSession(site=site, username=username, encrypted_secret=secret)
        session.audit.append("created")
        self.sessions[f"{site}:{username}"] = session
        return session

    def login_and_action(self, session: AccountSession, action_spec: Dict) -> Dict:
        self._check_policy(session.site)
        session.logged_in = True
        session.audit.append(f"action:{action_spec.get('type','unknown')}")
        return {"ok": True, "dev_mode": settings.dev_mode}

    def post_content(self, session: AccountSession, content: Dict) -> Dict:
        if not session.logged_in:
            raise ValueError("must login first")
        session.audit.append("post_content")
        return {"status": "posted", "len": len(content.get("body", ""))}
