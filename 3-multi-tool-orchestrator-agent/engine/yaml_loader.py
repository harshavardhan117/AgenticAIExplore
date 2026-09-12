"""Safe, local YAML loading for GitLab CI configuration files."""

from pathlib import Path

import yaml

from engine.models import LoadedYamlDocument

DEFAULT_MAX_FILE_SIZE_BYTES = 1_048_576


class YamlLoadError(Exception):
    """Raised when a YAML file cannot be safely read or parsed."""


class YamlLoader:
    """Loads one local YAML mapping without constructing arbitrary Python objects."""

    def __init__(self, max_file_size_bytes: int = DEFAULT_MAX_FILE_SIZE_BYTES) -> None:
        if max_file_size_bytes <= 0:
            raise ValueError("max_file_size_bytes must be greater than zero")

        self._max_file_size_bytes = max_file_size_bytes

    def load(self, yaml_path: Path) -> LoadedYamlDocument:
        """Read and parse the YAML file at ``yaml_path``."""
        resolved_path = self._resolve_file(yaml_path)
        self._validate_size(resolved_path)

        try:
            content = resolved_path.read_text(encoding="utf-8-sig")
        except OSError as error:
            raise YamlLoadError(f"Unable to read YAML file: {resolved_path}") from error

        try:
            parsed_content = yaml.safe_load(content)
        except yaml.YAMLError as error:
            raise YamlLoadError(self._format_yaml_error(resolved_path, error)) from error

        if not isinstance(parsed_content, dict):
            raise YamlLoadError(
                f"GitLab CI YAML must contain a mapping at its root: {resolved_path}"
            )

        if not all(isinstance(key, str) for key in parsed_content):
            raise YamlLoadError(
                f"GitLab CI YAML root keys must be strings: {resolved_path}"
            )

        return LoadedYamlDocument(source_file=resolved_path, content=parsed_content)

    @staticmethod
    def _resolve_file(yaml_path: Path) -> Path:
        try:
            resolved_path = yaml_path.resolve(strict=True)
        except FileNotFoundError as error:
            raise YamlLoadError(f"YAML file does not exist: {yaml_path}") from error
        except OSError as error:
            raise YamlLoadError(f"Unable to resolve YAML file: {yaml_path}") from error

        if not resolved_path.is_file():
            raise YamlLoadError(f"YAML path is not a file: {resolved_path}")

        if resolved_path.suffix.lower() not in {".yml", ".yaml"}:
            raise YamlLoadError(
                f"YAML file must use a .yml or .yaml extension: {resolved_path}"
            )

        return resolved_path

    def _validate_size(self, yaml_path: Path) -> None:
        try:
            file_size = yaml_path.stat().st_size
        except OSError as error:
            raise YamlLoadError(f"Unable to inspect YAML file: {yaml_path}") from error

        if file_size > self._max_file_size_bytes:
            raise YamlLoadError(
                "YAML file exceeds the configured size limit "
                f"({self._max_file_size_bytes} bytes): {yaml_path}"
            )

    @staticmethod
    def _format_yaml_error(yaml_path: Path, error: yaml.YAMLError) -> str:
        problem_mark = getattr(error, "problem_mark", None)
        if problem_mark is None:
            return f"Malformed YAML in {yaml_path}: {error}"

        return (
            f"Malformed YAML in {yaml_path} at line {problem_mark.line + 1}, "
            f"column {problem_mark.column + 1}: {error}"
        )
