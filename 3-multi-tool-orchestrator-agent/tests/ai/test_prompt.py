from domain.models import AIReviewInput, AnalysisResult, Finding, FindingSeverity
from ai.prompt import build_prompt, parse_response


def _sample_input() -> AIReviewInput:
    finding = Finding(
        id="cycle-detected",
        severity=FindingSeverity.ERROR,
        title="Dependency cycle detected",
        description="job_a and job_b depend on each other.",
    )
    analysis = AnalysisResult(
        is_acyclic=False,
        execution_layers=[],
        root_job_ids=[],
        terminal_job_ids=[],
        findings=[finding],
    )
    return AIReviewInput(validation_findings=[], analysis=analysis)


def test_build_prompt_includes_finding_and_json_instruction():
    prompt = build_prompt(_sample_input())

    assert "cycle-detected" in prompt
    assert "Dependency cycle detected" in prompt
    assert '"reviews"' in prompt


def test_parse_response_handles_plain_json():
    raw = '{"reviews": [{"finding_id": "cycle-detected", "explanation": "x", "priority": 1, "impact_estimate": "y"}]}'

    output = parse_response(raw)

    assert len(output.reviews) == 1
    assert output.reviews[0].finding_id == "cycle-detected"


def test_parse_response_handles_fenced_json():
    raw = '```json\n{"reviews": []}\n```'

    output = parse_response(raw)

    assert output.reviews == []
