"""CLI entry point. Thin wrapper: parse args, call the orchestrator, print the result."""

import argparse
import sys
from pathlib import Path

from dotenv import load_dotenv

from orchestrator import run


def main() -> None:
    load_dotenv()

    parser = argparse.ArgumentParser(description="Analyze a GitLab CI pipeline YAML file.")
    parser.add_argument("yaml_path", type=Path, help="Path to the .gitlab-ci.yml file")
    parser.add_argument("--ai", action="store_true", help="Also run the optional AI review step")
    args = parser.parse_args()

    try:
        report = run(args.yaml_path, ai_mode=args.ai)
    except (ValueError, FileNotFoundError) as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    print(report.report_markdown)
    print("\n## Mermaid\n")
    print(report.mermaid)

    if args.ai:
        print("\n## AI review\n")
        if report.ai_error:
            print(report.ai_error)
        else:
            for item in report.ai_review.reviews:
                print(f"- [{item.priority}] {item.finding_id}: {item.explanation} (impact: {item.impact_estimate})")


if __name__ == "__main__":
    main()
