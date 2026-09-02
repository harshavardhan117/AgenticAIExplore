# Embedding pipeline

The embedding pipeline turns `Chunk` records into `EmbeddedChunk` records. It separates provider-specific SDK calls from the generic record shape used by storage backends.

It is reusable for chunks from any Confluence collection. The current registered provider is OCI; the contract and factory allow another embedding provider to be added without changing the record or storage layers.

It is reusable for chunks from any Confluence collection. The current registered provider is OCI; the contract and factory allow another embedding provider to be added without changing the record or storage layers.

```text
Chunk JSON -> build embedding text -> EmbeddingProvider -> EmbeddedChunk JSON
```

## Packages

- `embeddings/`: provider contracts, factory, OCI configuration, and OCI implementation.
- `records/`: builds model-ready text, creates `EmbeddedChunk` records, and writes private embedded JSON.

## Provider design

`EmbeddingProvider` defines `embed(request)`. `EmbeddingProviderFactory` chooses a registered provider by name. OCI is registered today; another provider can be added by implementing the same contract and registering a builder.

## Run it

First preview the estimated input cost without making model calls:

```powershell
python .\embed_all_chunks.py
```

Then generate missing embeddings:

```powershell
python .\embed_all_chunks.py --all
```

OCI configuration comes from environment variables, including `OCI_CONFIG_FILE_PATH`, `OCI_PROFILE_NAME`, `OCI_COMPARTMENT_ID`, `OCI_ENDPOINT`, and `OCI_EMBEDDING_MODEL_ID`.

All five variables are required except `OCI_CONFIG_FILE_PATH` (default: `~/.oci/config`) and `OCI_PROFILE_NAME` (default: `DEFAULT`). Put them in the root ignored `.env` file or export them in the shell; exports take precedence. The root README has PowerShell and Bash examples.

All five variables are required except `OCI_CONFIG_FILE_PATH` (default: `~/.oci/config`) and `OCI_PROFILE_NAME` (default: `DEFAULT`). Put them in the root ignored `.env` file or export them in the shell; exports take precedence. The root README has PowerShell and Bash examples.

The output embeds page title, heading path, content type, and chunk content as one text input. Metadata remains separate in the resulting record so citations do not depend on reverse-engineering the vector.
