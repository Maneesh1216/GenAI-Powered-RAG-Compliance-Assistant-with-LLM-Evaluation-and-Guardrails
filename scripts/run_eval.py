#!/usr/bin/env python3
"""Run the golden-set evaluation and record the results."""

import signal

# Piping to `head` closes stdout early; without this Python raises
# BrokenPipeError and prints a traceback that looks like a crash.
try:
    signal.signal(signal.SIGPIPE, signal.SIG_DFL)
except (AttributeError, ValueError):  # not available on Windows
    pass

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from compliance_assistant.config import settings
from compliance_assistant.evaluation import run_evaluation
from compliance_assistant.pipeline import ComplianceAssistant
from compliance_assistant.tracking import Tracker


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate the RAG pipeline")
    parser.add_argument("--cases", default=str(ROOT / "eval" / "questions.yaml"))
    parser.add_argument("--out", default=str(ROOT / "eval" / "results"))
    parser.add_argument("--prompt-version", default=settings.prompt_version)
    parser.add_argument("--top-k", type=int, default=settings.top_k)
    args = parser.parse_args()

    settings.prompt_version = args.prompt_version
    settings.top_k = args.top_k

    assistant = ComplianceAssistant.from_index()
    report = run_evaluation(assistant, Path(args.cases), Path(args.out))
    summary = report["summary"]

    with Tracker(run_name=f"eval-{args.prompt_version}-k{args.top_k}") as tracker:
        tracker.log_params({
            "prompt_version": args.prompt_version,
            "top_k": args.top_k,
            "embedder": summary["embedder"],
            "llm": summary["llm"],
            "retrieval_backend": summary["retrieval_backend"],
        })
        tracker.log_metrics(summary)

    print(json.dumps(summary, indent=2))

    failures = [r for r in report["results"] if not r["refusal_correct"] or not r["contains_expected"]]
    if failures:
        print(f"\n{len(failures)} case(s) below expectation:")
        for f in failures:
            print(f"  [{f['id']}] {f['question']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
