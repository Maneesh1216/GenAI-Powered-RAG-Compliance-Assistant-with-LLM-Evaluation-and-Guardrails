"""Streamlit UI.  Run: streamlit run app/streamlit_app.py"""

import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from compliance_assistant.pipeline import ComplianceAssistant  # noqa: E402

st.set_page_config(page_title="Compliance Assistant", page_icon="§", layout="wide")


@st.cache_resource
def load() -> ComplianceAssistant:
    return ComplianceAssistant.from_index()


assistant = load()

st.title("Compliance Assistant")
st.caption("Citation-backed answers over enterprise policy documents. Answers come only from the indexed corpus.")

with st.sidebar:
    st.subheader("Runtime")
    st.write(f"**Chunks indexed** {len(assistant.store.chunks)}")
    st.write(f"**Embedder** `{assistant.embedder.name}`")
    st.write(f"**Vector backend** `{assistant.store.vector.backend}`")
    st.write(f"**Generator** `{assistant.llm.name}`")
    st.write(f"**Prompt** `{assistant.cfg.prompt_version}`")
    if assistant.llm.name == "extractive":
        st.warning(
            "No LLM key configured. Answers are extracted verbatim from the "
            "retrieved sections rather than synthesised. Set OPENAI_API_KEY or "
            "ANTHROPIC_API_KEY for generated answers."
        )
    top_k = st.slider("Sections retrieved", 1, 10, assistant.cfg.top_k)

    st.divider()
    st.subheader("Corpus")
    docs = sorted({c.source for c in assistant.store.chunks})
    for doc in docs:
        st.caption(doc)

question = st.text_input(
    "Question", placeholder="e.g. What is the retention period for audit logs?"
)

examples = [
    "How long must transaction records be retained?",
    "What encryption standard is used for PHI at rest?",
    "Which role can grant and revoke warehouse roles?",
    "How many days of parental leave do we get?",
]
cols = st.columns(len(examples))
for col, example in zip(cols, examples):
    if col.button(example, use_container_width=True):
        question = example

if question:
    with st.spinner("Retrieving…"):
        answer = assistant.ask(question, top_k=top_k)

    if answer.refused:
        st.info(answer.text)
        st.caption("Refusing is the correct behaviour when the corpus does not cover a question.")
    else:
        st.markdown(answer.text)

    a, b, c = st.columns(3)
    a.metric("Groundedness", f"{answer.groundedness:.2f}")
    b.metric("Latency", f"{answer.latency_ms} ms")
    c.metric("Sections used", len(answer.hits))

    if answer.hits:
        st.subheader("Retrieved sections")
        for i, hit in enumerate(answer.hits, start=1):
            cited = any(c.marker == i for c in answer.citations)
            label = f"[{i}] {hit.chunk.citation} — {hit.matched_by} match" + ("  ✓ cited" if cited else "")
            with st.expander(label, expanded=cited):
                st.write(hit.chunk.text)
                st.caption(f"fusion score {hit.score:.4f}")
