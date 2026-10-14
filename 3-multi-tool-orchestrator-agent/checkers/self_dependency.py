"""Flags a job that lists itself in its own `needs`. A trivial cycle, but worth its own clear message."""

from checkers.base import Checker
from domain.models import Finding, FindingSeverity, PipelineDefinition


class SelfDependencyChecker(Checker):
    def check(self, pipeline: PipelineDefinition) -> list[Finding]:
        findings: list[Finding] = []
        for job_id, job in pipeline.jobs.items():
            if job_id in job.needs:
                findings.append(
                    Finding(
                        id=f"self-dependency-{job_id}",
                        severity=FindingSeverity.ERROR,
                        title="Job depends on itself",
                        description=f"Job '{job_id}' lists itself in its own 'needs'.",
                        evidence=[job.source_location],
                    )
                )
        return findings
