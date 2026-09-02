# Confluence chunking

This module converts a raw Confluence page snapshot into retrieval-sized records while preserving citation metadata and order.

It is reusable for any storage-format Confluence snapshot produced by the ingestion module. It has no environment-variable requirements.

It is reusable for any storage-format Confluence snapshot produced by the ingestion module. It has no environment-variable requirements.

## Flow

1. `html_parser.py` reads Confluence storage-format HTML and emits ordered `ParsedBlock` objects such as headings, paragraphs, tables, and code blocks.
2. A strategy groups those blocks into `Chunk` objects.
3. `json_writer.py` saves each page's chunk records under `data/chunks/<strategy>/`.

`ParsedBlock` is the smallest meaningful parsed unit. A `Chunk` is the retrieval unit that will later receive one embedding.

## Strategies

- `section_as_chunk_v1` (`section_strategy.py`): combines a heading path with its section content. This is the default minimal-cost strategy.
- `structural_window_v1` (`structural_strategy.py`): creates overlapping structural windows. It gives more context but creates more embeddings.

Factories and interfaces make it possible to add another strategy without changing the pipeline driver.

## Run the default strategy

```powershell
python .\chunk_all_pages.py
```

```bash
python chunk_all_pages.py
```

```bash
python chunk_all_pages.py
```

The command reads `data/raw_pages/` and writes `data/chunks/section_as_chunk_v1/` by default. Both locations are private local artifacts.

## When to use it

Run chunking after an ingestion refresh and before embedding. Re-running is safe: each page's chunk JSON is regenerated from its current raw snapshot.
