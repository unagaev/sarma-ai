# SARMA — Architecture

## Overview

SARMA is a Retrieval-Augmented Generation (RAG) assistant over local PDF documents (currently: a UK agronomy nutrient-management guide and the Sentinel-2 satellite product specification), answering natural-language questions with citations back to source document and page.

```
┌──────────────┐   ┌───────────┐   ┌────────────────┐   ┌──────────────────┐
│  PDF corpus  │──▶│  loader   │──▶│    splitter     │──▶│  BGE embeddings   │
│ data/         │   │(per-page  │   │(RecursiveChar-  │   │(local, via        │
│ knowledge_base│   │ metadata) │   │ Splitter,       │   │ HuggingFace)      │
└──────────────┘   └───────────┘   │ 1000/200)       │   └────────┬──────────┘
                                    └────────────────┘            │
                                                                   ▼
                                                          ┌──────────────────┐
                                                          │  Chroma vector    │
                                                          │  store (local,    │
                                                          │  persisted)       │
                                                          └────────┬──────────┘
                                                                   │
    question ─────────────────────────────────────────────────────┤
                                                                   ▼
                                                        ┌────────────────────┐
                                                        │  retrieve (+score)  │
                                                        └──────────┬──────────┘
                                                                   ▼
                                                     ┌── conditional edge ──┐
                                          confident   │                      │  not confident
                                          match        ▼                      ▼
                                                ┌──────────────┐     ┌──────────────────┐
                                                │   generate    │     │    no_context     │
                                                │ (Ollama LLM,  │     │ (explicit refusal, │
                                                │  grounded)    │     │  no LLM call)      │
                                                └──────┬────────┘     └─────────┬──────────┘
                                                       ▼                        ▼
                                                answer + citations      "I don't have enough
                                                                          information"
```

## Components

| Module | Responsibility |
|---|---|
| `src/sarma/ingestion/loader.py` | Loads a single PDF via `PyPDFLoader`, tags each page with `source` (filename) and human-numbered `page` metadata. |
| `src/sarma/ingestion/knowledge_base.py` | Walks `data/knowledge_base/` for all PDFs and loads them via `loader.py`. |
| `src/sarma/ingestion/splitter.py` | Splits loaded documents into ~1000-character chunks (200 overlap) via `RecursiveCharacterTextSplitter`, preserving metadata on every chunk. |
| `src/sarma/embeddings.py` | Defines the embedding model: `BAAI/bge-small-en-v1.5`, run locally via `langchain_huggingface`. |
| `src/sarma/vectorstore/vectorstore.py` | Creates/loads a local, persisted Chroma collection (`data/chroma_db`) from chunks + embeddings. |
| `src/sarma/retriever.py` | Wraps the vector store as a LangChain retriever (`k=5`). |
| `src/sarma/prompts.py` | The RAG prompt: answer only from provided context, explicitly refuse ("I don't have enough information") if the context doesn't contain the answer. |
| `src/sarma/llm.py` | The generation model: `ChatOllama(model="qwen3:8b", temperature=0)`, run locally. |
| `src/sarma/citations.py` | Formats retrieved-document metadata into a deduplicated `"source, page N"` citation list. |
| `src/sarma/graph/state.py` | The shared `SarmaState` (question, documents, context, answer, citations, best_score, sufficient_context) passed between graph nodes. |
| `src/sarma/graph/nodes.py` | The graph's node functions: `retrieve_node` (retrieval + similarity score + confidence check), `generate_node` (grounded LLM generation), `no_context_node` (explicit refusal), `route_by_relevance` (the conditional edge). |
| `src/sarma/graph/workflow.py` | Assembles the nodes into a compiled LangGraph `StateGraph`: `retrieve → [generate \| no_context]`. |
| `src/sarma/graph/guardrails.py` | An optional, not-yet-wired-in input guardrail node (pattern-based prompt-injection screening) — see the module docstring for how to add it. |
| `src/sarma/assistant.py` / `src/sarma/rag/rag.py` | A simpler, non-graph implementation of the same retrieve→generate flow (a `SarmaAssistant` class and a plain LCEL chain respectively) — kept alongside the graph version as a direct point of comparison. |

## Two implementations, one pipeline

The repo intentionally contains two ways of running the same retrieve→generate logic:

1. **`create_rag_chain` / `SarmaAssistant`** — a plain LangChain chain / class. Simple, linear, easy to read.
2. **`create_sarma_graph`** — a LangGraph `StateGraph`. Same retrieval and generation logic, but expressed as nodes and edges over shared state, with a conditional branch based on retrieval confidence.

At the current scope, (2) does something (1) can't express as cleanly: skip generation entirely when retrieval isn't confident, rather than always calling the LLM and hoping the prompt's refusal instruction is followed. See `docs/decisions.md` for the fuller reasoning and what would justify moving further node-based logic (guardrails, reranking, multi-step reasoning) into the graph.

## Data flow guarantees

- Every chunk carries `source` (PDF filename) and `page` (1-indexed) metadata from ingestion through to the final citation list — nothing in the pipeline drops this.
- Generation is always grounded: the prompt receives only retrieved chunk content, and the graph now enforces a minimum similarity confidence before generation is attempted at all (see Tier 2 in `docs/roadmap.md`).
- Everything (embeddings, vector store, LLM) runs locally — no document content or question is sent to a third-party API.

## Known gaps (tracked in `docs/roadmap.md`)

- Vector store ingestion is not yet idempotent (re-running ingestion can duplicate chunks).
- The similarity-score threshold used for routing (`DEFAULT_SCORE_THRESHOLD` in `nodes.py`) is a placeholder pending tuning against `notebooks/05_retrieval_eval.ipynb`.
- The guardrail node exists but isn't wired into the default graph.
