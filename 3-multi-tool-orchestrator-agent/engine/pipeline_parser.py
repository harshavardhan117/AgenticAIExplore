"""Extract the initial supported GitLab CI concepts from loaded YAML."""

from pathlib import Path
from typing import Any

from engine.models import LoadedYamlDocument, PipelineDefinition
from engine.models import JobDefinition, SourceLocation

DEFAULT_STAGES = (".pre", "build", "test", "deploy", ".post")

# These top-level keys configure GitLab CI itself rather than define executable
# jobs. New supported global keywords belong here as the parser grows.
GLOBAL_KEYWORDS = frozenset(
    {
        "after_script",
        "before_script",
        "cache",
        "default",
        "image",
        "include",
        "services",
        "spec",
        "stages",
        "variables",
        "workflow",
    }
)


class PipelineParseError(Exception):
    """Raised when supported GitLab CI concepts cannot be interpreted."""


class GitLabPipelineParser:
    """Extracts the supported GitLab CI concepts from raw YAML content."""

    def parse(self, document: LoadedYamlDocument) -> PipelineDefinition:
        """Convert one loaded YAML document into a pipeline definition."""
        stages = self._parse_stages(document.content, document.source_file)
        jobs = self._parse_jobs(document.content, document.source_file, stages)

        if not jobs:
            raise PipelineParseError("GitLab CI configuration contains no visible jobs")

        return PipelineDefinition(
            source_file=document.source_file,
            stages=stages,
            jobs=jobs,
        )

    @staticmethod
    def _parse_stages(content: dict[str, Any], source_file: Path) -> list[str]:
        raw_stages = content.get("stages", list(DEFAULT_STAGES))
        location = SourceLocation(file_path=source_file, yaml_path="stages")

        if not isinstance(raw_stages, list) or not all(
            isinstance(stage, str) and stage.strip() for stage in raw_stages
        ):
            raise PipelineParseError(
                f"{location.yaml_path} must be a list of non-empty stage names"
            )

        if len(set(raw_stages)) != len(raw_stages):
            raise PipelineParseError("stages must not contain duplicate stage names")

        return raw_stages

    def _parse_jobs(
        self,
        content: dict[str, Any],
        source_file: Path,
        stages: list[str],
    ) -> dict[str, JobDefinition]:
        jobs: dict[str, JobDefinition] = {}

        for job_id, raw_job in content.items():
            if self._is_non_executable_top_level_key(job_id):
                continue

            if not isinstance(raw_job, dict):
                raise PipelineParseError(f"Job '{job_id}' must be a YAML mapping")

            jobs[job_id] = self._parse_job(job_id, raw_job, source_file, stages)

        return jobs

    @staticmethod
    def _is_non_executable_top_level_key(key: str) -> bool:
        return key in GLOBAL_KEYWORDS or key.startswith(".")

    def _parse_job(
        self,
        job_id: str,
        raw_job: dict[str, Any],
        source_file: Path,
        stages: list[str],
    ) -> JobDefinition:
        stage = raw_job.get("stage", "test")
        if not isinstance(stage, str) or not stage.strip():
            raise PipelineParseError(f"Job '{job_id}' has an invalid stage")

        if stage not in stages:
            raise PipelineParseError(
                f"Job '{job_id}' references undefined stage '{stage}'"
            )

        needs = self._parse_needs(job_id, raw_job.get("needs"))

        return JobDefinition(
            id=job_id,
            stage=stage,
            needs=needs,
            source_location=SourceLocation(file_path=source_file, yaml_path=job_id),
        )

    @staticmethod
    def _parse_needs(job_id: str, raw_needs: Any) -> list[str]:
        if raw_needs is None:
            return []

        if isinstance(raw_needs, str):
            return [raw_needs]

        if isinstance(raw_needs, list) and all(
            isinstance(need, str) and need.strip() for need in raw_needs
        ):
            return raw_needs

        raise PipelineParseError(
            f"Job '{job_id}' uses unsupported 'needs' syntax; "
            "V1 supports a job name or a list of job names"
        )
