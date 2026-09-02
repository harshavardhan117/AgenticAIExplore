# RAG evaluation

This module evaluates a complete dense-vector RAG flow. It runs a query through embedding, retrieval, the grounded answer model, and evaluator logic, then writes a local JSON report.

## Private dataset shape

Create `data/evaluation/my_eval_set.json` locally. It must not be committed because it may reveal internal questions, expected answers, and source URLs.

```json
[
  {
    "id": "eval-001",
    "question": "How do I configure the deployment?",
    "reference_answer": "A short reviewer-authored answer, if available.",
    "expected_source_urls": ["https://confluence.example.com/pages/viewpage.action?pageId=123"],
    "expected_keywords": ["configuration"],
    "should_abstain": false
  },
  {
    "id": "eval-002",
    "question": "What is the policy for an unrelated product?",
    "reference_answer": "I cannot answer reliably from the retrieved Confluence documentation.",
    "expected_source_urls": [],
    "expected_keywords": [],
    "should_abstain": true
  }
]
```

## Run all enabled metrics

```powershell
python .\evaluate_rag.py --backend oracle --retrieval-strategy dense --limit 5 `
  --dataset-path .\data\evaluation\my_eval_set.json `
  --output-path .\data\evaluation\runs\oracle_metrics.json
```

Choose one of `--retrieval-strategy dense`, `keyword`, or `hybrid_rrf`. Repeat with `--backend opensearch` to compare the two vector stores under the same dataset, model configuration, strategy, and top-K limit. Keyword retrieval reads SQLite FTS5 and is therefore backend-independent; hybrid uses the chosen vector backend for dense candidates and SQLite for keyword candidates.

## Metrics

| Metric | What it checks |
| --- | --- |
| Hit@K | Whether any expected source appears in the top K retrieved page URLs. |
| MRR@K | How early the first expected source appears; rank 1 scores `1.0`, rank 2 scores `0.5`. |
| Answer relevancy | Whether the generated answer addresses the user question. It is scored by the configured chat model. |
| Citation correctness | Whether cited `[Source N]` chunks support the answer's claims. It is scored by the configured chat model. |
| Abstention accuracy | Whether the RAG answers supported questions and abstains for unsupported ones. |

## Interpretation

Hit@K and MRR measure retrieval only. Answer relevancy and citation correctness measure generation quality and grounding. Abstention accuracy catches both hallucinations on unsupported questions and needless refusal on supported questions.

The LLM-as-judge metrics are useful prototype signals, not absolute truth: use a separate judge model or human review before presenting results as a production benchmark.
