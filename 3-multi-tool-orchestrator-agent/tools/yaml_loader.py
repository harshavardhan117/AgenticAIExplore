"""Reads a YAML file off disk into a LoadedYamlDocument."""

from pathlib import Path

import yaml

from domain.models import LoadedYamlDocument
from observability.tool_logging import log_tool_call


@log_tool_call
def load_yaml_document(path: Path) -> LoadedYamlDocument:
    content = yaml.safe_load(path.read_text())

    if not isinstance(content, dict):
        raise ValueError(f"{path}: expected a YAML mapping at the top level, got {type(content).__name__}")

    return LoadedYamlDocument(source_file=path, content=content)
