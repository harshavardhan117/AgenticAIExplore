"""Convert Confluence storage-format HTML into a shared structured-page form."""

from __future__ import annotations

from dataclasses import dataclass, field
from html.parser import HTMLParser
from pathlib import Path
from typing import Any, Mapping
import json
import re

from source_processing.chunking.data_models import ParsedBlock, ParsedPage


_HEADING_RE = re.compile(r"h([1-6])$")
_VOID_TAGS = {"br", "hr", "img", "meta", "link", "input"}


@dataclass
class _Node:
    """A deliberately small HTML tree used only by this parser."""

    tag: str
    attributes: dict[str, str]
    children: list[_Node | str] = field(default_factory=list)


class _HtmlTreeBuilder(HTMLParser):
    """Build enough of an HTML tree to preserve Confluence block order."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.root = _Node(tag="document", attributes={})
        self._stack = [self.root]

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        node = _Node(
            tag=tag.lower(),
            attributes={name.lower(): value or "" for name, value in attrs},
        )
        self._stack[-1].children.append(node)
        if node.tag not in _VOID_TAGS:
            self._stack.append(node)

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.handle_starttag(tag, attrs)
        if tag.lower() not in _VOID_TAGS:
            self.handle_endtag(tag)

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        for index in range(len(self._stack) - 1, 0, -1):
            if self._stack[index].tag == tag:
                del self._stack[index:]
                return

    def handle_data(self, data: str) -> None:
        self._stack[-1].children.append(data)


def parse_raw_page(raw_page: Mapping[str, Any]) -> ParsedPage:
    """Parse one saved raw-page JSON object into ordered structural blocks."""

    page_id = _required_text(raw_page, "page_id")
    page_title = _required_text(raw_page, "title")
    page_url = _required_text(raw_page, "page_url")
    raw_html = _required_text(raw_page, "raw_content_html")
    source_version = raw_page.get("version")
    if not isinstance(source_version, int) or source_version < 1:
        raise ValueError("raw page field 'version' must be a positive integer")

    builder = _HtmlTreeBuilder()
    builder.feed(raw_html)
    builder.close()

    blocks = _extract_blocks(builder.root, page_title)
    return ParsedPage(
        page_id=page_id,
        page_title=page_title,
        page_url=page_url,
        source_version=source_version,
        blocks=blocks,
    )


def parse_raw_page_file(path: Path) -> ParsedPage:
    """Load and parse one raw snapshot written by the ingestion collector."""

    with path.open(encoding="utf-8") as raw_page_file:
        raw_page = json.load(raw_page_file)
    if not isinstance(raw_page, dict):
        raise ValueError(f"Expected a JSON object in {path}")
    return parse_raw_page(raw_page)


def _extract_blocks(root: _Node, page_title: str) -> list[ParsedBlock]:
    heading_levels: dict[int, str] = {}
    blocks: list[ParsedBlock] = []

    def current_path() -> list[str]:
        return [heading_levels[level] for level in sorted(heading_levels)] or [page_title]

    def visit(node: _Node | str) -> None:
        if isinstance(node, str):
            return

        heading_match = _HEADING_RE.fullmatch(node.tag)
        if heading_match:
            level = int(heading_match.group(1))
            heading = _node_text(node)
            if heading:
                heading_levels[level] = heading
                for deeper_level in range(level + 1, 7):
                    heading_levels.pop(deeper_level, None)
            return

        if node.tag == "table":
            content = _table_text(node)
            if content:
                blocks.append(
                    ParsedBlock(
                        position=len(blocks),
                        heading_path=current_path(),
                        block_type="table",
                        content=content,
                    )
                )
            return

        if node.tag == "pre" or _is_code_macro(node):
            content = _node_text(node)
            if content:
                blocks.append(
                    ParsedBlock(
                        position=len(blocks),
                        heading_path=current_path(),
                        block_type="code",
                        content=content,
                    )
                )
            return

        if node.tag in {"p", "li"}:
            content = _node_text(node)
            if content:
                blocks.append(
                    ParsedBlock(
                        position=len(blocks),
                        heading_path=current_path(),
                        block_type="text",
                        content=content,
                    )
                )
            return

        for child in node.children:
            visit(child)

    visit(root)
    return blocks


def _required_text(raw_page: Mapping[str, Any], field_name: str) -> str:
    value = raw_page.get(field_name)
    if value is None:
        raise ValueError(f"raw page is missing required field: {field_name}")
    text = str(value).strip()
    if not text:
        raise ValueError(f"raw page field '{field_name}' must contain text")
    return text


def _is_code_macro(node: _Node) -> bool:
    return (
        node.tag == "ac:structured-macro"
        and node.attributes.get("ac:name", "").lower() == "code"
    )


def _node_text(node: _Node) -> str:
    pieces: list[str] = []

    def collect(child: _Node | str) -> None:
        if isinstance(child, str):
            pieces.append(child)
            return
        if child.tag == "br":
            pieces.append("\n")
            return
        for nested_child in child.children:
            collect(nested_child)

    collect(node)
    return re.sub(r"[ \t]+", " ", "".join(pieces)).strip()


def _table_text(table: _Node) -> str:
    rows: list[str] = []

    def find_rows(node: _Node | str) -> None:
        if isinstance(node, str):
            return
        if node.tag == "tr":
            cells = [
                _node_text(cell)
                for cell in node.children
                if isinstance(cell, _Node) and cell.tag in {"th", "td"}
            ]
            if cells:
                rows.append(" | ".join(cells))
            return
        for child in node.children:
            find_rows(child)

    find_rows(table)
    return "\n".join(rows)
