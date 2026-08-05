#!/usr/bin/env python3
"""Build and persist the hybrid index from the policy corpus."""

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

from compliance_assistant.config import settings
from compliance_assistant.embeddings import get_embedder
from compliance_assistant.ingest import chunk_documents
from compliance_assistant.retriever import build_store


def main() -> int:
    parser = argparse.ArgumentParser(description="Build the compliance document index")
    parser.add_argument("--corpus", default=str(settings.corpus_dir))
    parser.add_argument("--out", default=str(settings.index_dir))
    parser.add_argument("--no-transformer", action="store_true",
                        help="force the hashing embedder even if sentence-transformers is installed")
    args = parser.parse_args()

    settings.corpus_dir = Path(args.corpus)
    embedder = get_embedder(prefer_transformer=not args.no_transformer)

    print(f"corpus     : {settings.corpus_dir}")
    chunks = chunk_documents(cfg=settings)
    print(f"chunks     : {len(chunks)}")
    print(f"embedder   : {embedder.name} (dim {embedder.dim})")

    store = build_store(chunks, embedder)
    store.save(Path(args.out))
    print(f"backend    : {store.vector.backend}")
    print(f"written to : {args.out}")

    sources = sorted({c.source for c in chunks})
    print(f"documents  : {len(sources)}")
    for src in sources:
        n = sum(1 for c in chunks if c.source == src)
        print(f"  - {src:<28} {n:>3} chunks")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
