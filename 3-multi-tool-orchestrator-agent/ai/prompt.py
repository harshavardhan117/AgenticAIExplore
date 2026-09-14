"""Shared prompt building + response parsing, used by every AI provider adapter."""

import re

from domain.models import AIReviewInput, AIReviewOutput

_JSON_FENCE = re.compile(r"```(?:json)?\s*(.*?)```", re.DOTALL)


def build_prompt(review_input: AIReviewInput) -> str:
    all_findings = review_input.validation_findings + review_input.analysis.findings
    findings_text = "\n".join(
        f"- id={f.id} severity={f.severity.value} title={f.title!r} description={f.description!r}"
        for f in all_findings
    ) or "(none)"

    analysis = review_input.analysis
    layers_text = "\n".join(
        f"  Layer {i + 1}: {', '.join(layer)}"
        for i, layer in enumerate(analysis.execution_layers)
    ) or "(none)"

    return f"""You are reviewing the deterministic analysis of a CI/CD pipeline.

Findings detected:
{findings_text}

Pipeline structure facts:
- Acyclic: {analysis.is_acyclic}
- Root jobs: {', '.join(analysis.root_job_ids) or 'none'}
- Terminal jobs: {', '.join(analysis.terminal_job_ids) or 'none'}
- Execution layers:
{layers_text}

For EACH finding listed above, provide a plain-language explanation, a priority
(1 = highest, 5 = lowest), and a short estimate of its productivity/time impact
if addressed. Do not invent new findings - only explain the ones listed above.

Respond with ONLY valid JSON matching this exact shape, no other text:
{{
  "reviews": [
    {{"finding_id": "<id>", "explanation": "<text>", "priority": <int 1-5>, "impact_estimate": "<text>"}}
  ]
}}
"""


def parse_response(raw_text: str) -> AIReviewOutput:
    text = raw_text.strip()
    fence_match = _JSON_FENCE.search(text)
    if fence_match:
        text = fence_match.group(1).strip()
    return AIReviewOutput.model_validate_json(text)
