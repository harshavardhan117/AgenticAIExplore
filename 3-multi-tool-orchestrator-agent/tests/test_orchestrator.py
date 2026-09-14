from pathlib import Path

from orchestrator import run

FIXTURE = Path(__file__).parent / "fixtures" / "simple_pipeline.yml"


def test_run_produces_full_report():
    report = run(FIXTURE)

    assert report.analysis.is_acyclic is True
    assert report.validation_findings == []
    assert "flowchart TD" in report.mermaid
    assert "## Execution layers" in report.report_markdown
    assert report.ai_review is None
    assert report.ai_error is None


def test_run_surfaces_dangling_needs_in_report():
    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        broken = Path(tmp) / "broken.gitlab-ci.yml"
        broken.write_text(
            FIXTURE.read_text()
            + "\nghost_job:\n  stage: test\n  needs: [nonexistent_job]\n"
        )

        report = run(broken)

        assert any(f.title == "Dangling needs reference" for f in report.validation_findings)
        assert "Dangling needs reference" in report.report_markdown
