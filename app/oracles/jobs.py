from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict


@dataclass
class ExternalJob:
    job_id: str
    service: str
    payload: Dict[str, Any]
    proof_required: bool = True


class JobOraclePipeline:
    def __init__(self) -> None:
        self.jobs: Dict[str, ExternalJob] = {}
        self.completed: set[str] = set()

    def submit_job(self, job: ExternalJob) -> None:
        self.jobs[job.job_id] = job

    def verify_result(self, job_id: str, proof: str) -> bool:
        job = self.jobs[job_id]
        if not job.proof_required:
            return True
        expected_prefix = f"proof:{job.service}:"
        return proof.startswith(expected_prefix)

    def complete_job(self, job_id: str, proof: str) -> bool:
        valid = self.verify_result(job_id, proof)
        if not valid:
            return False
        self.completed.add(job_id)
        return True
