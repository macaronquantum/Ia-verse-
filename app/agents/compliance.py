"""High-level policy checks for external jobs and marketplace safety."""

from __future__ import annotations


BLOCKLIST = {"doxx", "steal", "credential stuffing", "malware", "phishing", "bypass paywall"}


def is_job_safe(description: str) -> bool:
    content = description.lower()
    return not any(term in content for term in BLOCKLIST)
