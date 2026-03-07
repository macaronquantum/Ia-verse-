from __future__ import annotations

from dataclasses import dataclass
from typing import List


ALLOWED_PHYSICAL_KEYWORDS = ["delivery", "installation", "drone", "field", "warehouse", "pickup"]


@dataclass
class JobPosting:
    title: str
    location: str
    budget: float
    risky: bool = False
    accepted: bool = False


class JobMarket:
    def __init__(self) -> None:
        self.jobs: List[JobPosting] = []

    def post_job(self, job: JobPosting) -> JobPosting:
        low = job.title.lower()
        if not any(k in low for k in ALLOWED_PHYSICAL_KEYWORDS):
            raise ValueError("Only physical-world tasks are allowed for human hiring")
        self.jobs.append(job)
        return job
