#!/usr/bin/env python3
"""Ask a single question from the command line."""

import signal

# Piping to `head` closes stdout early; without this Python raises
# BrokenPipeError and prints a traceback that looks like a crash.
try:
    signal.signal(signal.SIGPIPE, signal.SIG_DFL)
except (AttributeError, ValueError):  # not available on Windows
    pass

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from compliance_assistant.pipeline import ComplianceAssistant


def main() -> int:
    parser = argparse.ArgumentParser(description="Query the compliance corpus")
    parser.add_argument("question", nargs="+")
    parser.add_argument("--k", type=int, default=None)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    assistant = ComplianceAssistant.from_index()
    answer = assistant.ask(" ".join(args.question), top_k=args.k)

    if args.json:
        import json
        print(json.dumps(answer.to_dict(), indent=2))
        return 0

    print(f"\n{answer.text}\n")
    print("-" * 62)
    for hit in answer.hits:
        print(f"  [{answer.hits.index(hit)+1}] {hit.chunk.citation}"
              f"  (score {hit.score:.4f}, {hit.matched_by})")
    print("-" * 62)
    print(f"  generated_by={answer.generated_by}  model={answer.model}")
    print(f"  groundedness={answer.groundedness}  latency={answer.latency_ms}ms")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
