"""Configuration for the local SQLite Confluence content catalog."""

from pathlib import Path

from pydantic import BaseModel


class SqliteCatalogConfig(BaseModel):
    """Location of the SQLite database file used for relational metadata."""

    database_path: Path
