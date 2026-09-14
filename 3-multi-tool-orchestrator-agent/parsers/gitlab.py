"""GitLab CI parser strategy — turns a .gitlab-ci.yml document into a PipelineDefinition."""

from domain.models import JobDefinition, LoadedYamlDocument, PipelineDefinition, SourceLocation
from parsers.base import Parser

_WEAK_JOB_KEYWORDS = {
    "artifacts", "needs", "stage", "rules", "only", "except",
    "extends", "before_script", "after_script", "image", "services",
    "cache", "tags", "when", "allow_failure",
}

_NON_JOB_KEYS = {
    "stages", "variables", "include", "default", "workflow",
    "image", "services", "cache", "before_script", "after_script",
}

_GITLAB_FILENAMES = {".gitlab-ci.yml", ".gitlab-ci.yaml"}
_CAN_PARSE_THRESHOLD = 2


class GitLabParser(Parser):
    """Parses GitLab CI YAML (.gitlab-ci.yml) into the common pipeline shape."""

    def can_parse(self, document: LoadedYamlDocument) -> bool:
        content = document.content

        # Negative signals: shapes that mean this is a different CI system entirely.
        if "on" in content and "jobs" in content:  # GitHub Actions
            return False
        if "pool" in content or "trigger" in content:  # Azure Pipelines
            return False

        score = 0

        stages = content.get("stages")
        if isinstance(stages, list) and all(isinstance(s, str) for s in stages):
            score += 2

        for value in content.values():
            if not isinstance(value, dict):
                continue
            if "script" in value:
                score += 2
            elif len(_WEAK_JOB_KEYWORDS & value.keys()) >= 2:
                score += 1

        if document.source_file.name in _GITLAB_FILENAMES:
            score += 1

        return score >= _CAN_PARSE_THRESHOLD

    def parse(self, document: LoadedYamlDocument) -> PipelineDefinition:
        content = document.content
        stages = content.get("stages", ["test"])

        jobs: dict[str, JobDefinition] = {}
        for key, value in content.items():
            if key in _NON_JOB_KEYS or key.startswith("."):
                continue
            if not isinstance(value, dict):
                continue
            jobs[key] = JobDefinition(
                id=key,
                stage=value.get("stage", "test"),
                needs=self._parse_needs(value.get("needs", [])),
                source_location=SourceLocation(file_path=document.source_file, yaml_path=key),
            )

        return PipelineDefinition(source_file=document.source_file, stages=stages, jobs=jobs)

    @staticmethod
    def _parse_needs(raw_needs: list) -> list[str]:
        needs: list[str] = []
        for entry in raw_needs:
            if isinstance(entry, str):
                needs.append(entry)
            elif isinstance(entry, dict) and "job" in entry:
                needs.append(entry["job"])
        return needs
