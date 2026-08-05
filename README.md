# RAG Compliance Assistant

Citation-backed Q&A over enterprise policy documents — retention standards,
RBAC policy, HIPAA safeguards, data quality rules, lineage requirements.

Ask *"how long must audit logs be retained?"* and get the answer with the clause
it came from. Ask something the corpus does not cover and get a refusal instead
of a plausible invention, which is the part that actually matters when the
reader is an auditor.

```
$ make index && make ask Q="What encryption standard is used for PHI at rest?"

Electronic protected health information is encrypted at rest using AES-256 with
keys held in the managed key service and rotated annually. [1]

--------------------------------------------------------------
  [1] 03-hipaa-safeguards.md § Encryption   (score 0.1893, both)
  [2] 03-hipaa-safeguards.md § Scope        (score 0.1194, dense)
--------------------------------------------------------------
  groundedness=0.87  latency=2ms
```

---

## Why this exists

Finding the clause that governs a dataset is a real recurring cost on a data
platform. The policy exists, someone wrote it, and nobody can find it during an
audit. This is a retrieval problem with an unusually low tolerance for made-up
answers.

That constraint shaped every design decision below.

---

## Running it

```bash
git clone <this repo> && cd rag-compliance-assistant
pip install -r requirements.txt     # numpy + PyYAML, nothing else
make index
make ask Q="how long are audit logs retained"
make eval
make test
```

No API key required. With no LLM configured the system runs in **extractive
mode**: it retrieves the right sections and quotes them verbatim rather than
synthesising, and says so in the output. Add a key for generated answers:

```bash
export OPENAI_API_KEY=sk-...        # or ANTHROPIC_API_KEY
make ask Q="..."
```

Optional upgrades, all detected automatically when installed:

| Install | Replaces |
|---|---|
| `sentence-transformers` | hashing embedder → real transformer embeddings |
| `faiss-cpu` | numpy matmul → ANN index |
| `mlflow` | JSONL run log → MLflow tracking |
| `pypdf` | markdown-only corpus → PDF ingestion |

`make install-full` gets all of them, plus FastAPI and Streamlit.

---

## Architecture

```
data/policies/*.md
      │
      ▼
  ingest.py ──── heading-aware split, sentence-safe windowing
      │
      ▼
  ┌─────────────────────────────┐
  │  BM25Index   VectorIndex    │   lexical + dense, built together
  └─────────────────────────────┘
      │
      ▼
  retriever.py ── weighted reciprocal rank fusion
      │
      ▼
  pipeline.py ─── coverage gate → refuse, or → prompt → LLM
      │
      ▼
  Answer(text, citations[], groundedness, refused)
```

### Chunking follows document structure

Compliance documents are structured — numbered clauses under headings. A fixed
character window cuts across that and produces chunks that cite the wrong
clause. `ingest.py` splits on headings first and only falls back to a
sentence-aware sliding window when a section is genuinely too long. Every chunk
carries `source` and `section`, so a citation resolves to
`03-hipaa-safeguards.md § Encryption` rather than "document 3, chunk 7".

### Retrieval is hybrid, and the fusion is weighted

Dense retrieval alone misses exact identifiers — `AES-256`, `DATA_ADMIN`,
`§164.312` — which is precisely what compliance questions ask about. BM25 alone
misses paraphrase. Both indexes run and their **ranks** are fused with RRF
rather than their scores, because cosine similarity and BM25 live on
incomparable scales and any fixed score blend has to be re-tuned every time the
embedder changes.

One tuning note worth recording: RRF's standard `k=60` comes from web-scale
candidate lists. On a corpus this size it compresses every rank into
near-identical scores, so a weak retriever cancels out a strong one. Dropping to
`k=10` restored rank sensitivity. This was not theoretical — with `k=60` the
correct chunk for *"how long must transaction records be retained"* ranked
**fourth** behind three irrelevant ones, despite BM25 having it first by a
factor of three.

### The no-dependency embedder is honest about being a fallback

`HashingEmbedder` exists so the project clones and runs with only numpy. The
first version was bad: naive character n-gram hashing retrieved worse than BM25
alone, because short queries produce few features and unweighted n-grams let
common English strings dominate. Weighting features by inverse document
frequency, fitted on the corpus at index time, fixed it — rare discriminating
terms now carry the signal.

It is still weaker than a transformer on genuine paraphrase. Every evaluation
result records which backend produced it, so the two are never silently
compared.

Its hash is FNV-1a, not Python's `hash()`, which is salted per process — a
persisted index built with `hash()` silently stops matching after a restart.

### Refusal is a pipeline decision, not a prompt instruction

Telling a model "say you don't know" is necessary and not sufficient. Before
generation, `query_coverage()` measures how much of the question's
**discriminating** vocabulary the retrieved context covers, weighted by corpus
IDF. Below `MIN_COVERAGE` the pipeline refuses without calling the model at all.

IDF weighting is the whole trick. Plain term overlap fails badly here: *"What is
the maximum permitted salary for a data engineer under the compensation
policy?"* overlaps an access-control clause on *maximum* and *data* while
sharing nothing that matters. Weighting by rarity collapses those common words
to near zero and lets *salary* and *compensation* — absent from the corpus, so
maximally rare — dominate.

Measured separation on the golden set:

| | coverage |
|---|---|
| in-scope questions | 0.59 – 0.68 |
| out-of-scope questions | 0.23 – 0.40 |
| threshold | 0.50 |

There is a regression test pinning the salary case specifically, because that
one shipped broken.

---

## Evaluation

`make eval` runs a golden set of 13 questions and writes metrics to
`eval/results/`, MLflow, and a local JSONL log.

Ten cases are answerable. **Three deliberately are not** — they sound plausible
and use in-domain vocabulary, but the corpus has nothing on them. Those exist
because the failure that matters most is a confident, well-cited answer to a
question the policy never addressed.

| Metric | What it catches |
|---|---|
| `hit_rate@k` | retrieval missed entirely — nothing downstream can recover |
| `mrr` | how high the first correct source ranked |
| `context_precision` | how much noise the generator was handed |
| `groundedness` | answer terms unsupported by retrieved context |
| `citation_validity` | every `[n]` marker resolves to a real chunk |
| `refusal_accuracy` | did it refuse when it should have |

Current run (hashing embedder, extractive generation, no API key):

```json
{
  "hit_rate": 1.0,
  "mrr": 0.7692,
  "context_precision": 0.3385,
  "groundedness": 0.817,
  "citation_validity": 1.0,
  "answer_correctness": 1.0,
  "refusal_accuracy": 1.0,
  "p95_latency_ms": 1
}
```

**Read these numbers in context.** They are measured on a five-document corpus
of 25 chunks with a hand-written question set — enough to catch regressions,
not enough to claim general performance. `context_precision` of 0.34 is the
honest weak spot: `top_k=5` on a corpus where most questions are answered by a
single chunk means most retrieved context is surplus. On a larger corpus that
number matters more and would want reranking.

Two of these metrics are only at 1.0 because the harness caught them failing
first. `refusal_accuracy` was 0.77 until the coverage gate was added.

`groundedness` is a floor, not a guarantee — it measures term overlap with
context, so it catches an answer that has drifted from its sources but not a
fluent claim assembled from words that all happen to appear.

---

## Prompt versioning

Prompts live in `prompts.py` under explicit versions (`v1`, `v2`, `v3`), and
every evaluation run logs `prompt_version`. Prompts are the component most
likely to change and the hardest to attribute after the fact; version them and a
drop in faithfulness traces to the edit that caused it.

```bash
python scripts/run_eval.py --prompt-version v2 --top-k 3
```

---

## Serving

```bash
make api    # FastAPI  → http://localhost:8000/docs
make ui     # Streamlit → http://localhost:8501
make docker
```

`GET /health` reports which embedder, vector backend and generator are live —
useful because the system silently degrades to fallbacks and you want that
visible rather than mysterious.

---

## Layout

```
src/compliance_assistant/
  config.py       env-driven settings
  ingest.py       loading, heading-aware chunking
  embeddings.py   transformer + IDF-weighted hashing fallback
  vectorstore.py  FAISS/numpy dense index, BM25 lexical index
  retriever.py    weighted RRF fusion
  prompts.py      versioned system prompts
  pipeline.py     orchestration, coverage gate, citation resolution
  evaluation.py   golden-set harness
  tracking.py     MLflow with JSONL fallback
  api.py          FastAPI
app/              Streamlit UI
scripts/          build_index, ask, run_eval
eval/             golden question set
tests/            17 tests
```

## Known limitations

- **Corpus is small and synthetic.** Five policy documents written for this
  repo. Retrieval numbers would look different on a real thousand-document
  corpus.
- **No reranker.** A cross-encoder over the fused candidates is the obvious next
  gain and would directly address the low context precision.
- **`groundedness` is lexical**, not entailment-based. A real faithfulness check
  needs an NLI model or LLM-as-judge scoring claim by claim.
- **No multi-hop.** Questions needing two clauses combined ("does the retention
  rule apply to the backup replica of a Restricted dataset?") retrieve both but
  rely entirely on the generator to join them.
- **Chunking assumes markdown headings.** PDF ingestion works but loses
  structure, so PDF-sourced chunks cite the document rather than the clause.
