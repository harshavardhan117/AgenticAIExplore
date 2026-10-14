"""Flags a job that has no dependencies and nothing depends on it — fully disconnected."""

from checkers.base import Checker
from domain.models import Finding, FindingSeverity, PipelineDefinition


class OrphanJobChecker(Checker):
    def check(self, pipeline: PipelineDefinition) -> list[Finding]:
        depended_on: set[str] = set()
        for job in pipeline.jobs.values():
            depended_on.update(job.needs)

        findings: list[Finding] = []
        for job_id, job in pipeline.jobs.items():
            if not job.needs and job_id not in depended_on:
                findings.append(
                    Finding(
                        id=f"orphan-job-{job_id}",
                        severity=FindingSeverity.WARNING,
                        title="Orphan job",
                        description=(
                            f"Job '{job_id}' has no dependencies and nothing depends on it — "
                            "it's fully disconnected from the rest of the pipeline."
                        ),
                        evidence=[job.source_location],
                    )
                )
        return findings
