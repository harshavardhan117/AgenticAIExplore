"""Flags a job assigned to a stage that isn't declared in the pipeline's `stages` list."""

from checkers.base import Checker
from domain.models import Finding, FindingSeverity, PipelineDefinition


class UndefinedStageChecker(Checker):
    def check(self, pipeline: PipelineDefinition) -> list[Finding]:
        findings: list[Finding] = []
        for job_id, job in pipeline.jobs.items():
            if job.stage not in pipeline.stages:
                findings.append(
                    Finding(
                        id=f"undefined-stage-{job_id}",
                        severity=FindingSeverity.ERROR,
                        title="Job assigned to undefined stage",
                        description=(
                            f"Job '{job_id}' is assigned to stage '{job.stage}', "
                            f"which is not declared in stages: {pipeline.stages}."
                        ),
                        evidence=[job.source_location],
                    )
                )
        return findings
