# SARMA — Roadmap

Status: ingestion → embeddings → Chroma → retriever → LangGraph (`retrieve` → `generate`, with confidence-based routing) runs end to end and produces correct, cited answers against the current knowledge base. Core pipeline is functional; the items below are hardening and polish, not new build-out.

Priority order: work top to bottom within each tier.

## Tier 1 — Fix first

- [ ] **Deduplicate vector store ingestion.** `notebooks/03_semantic_search.ipynb` shows every similarity-search result returned twice with identical scores — re-running ingestion into the same Chroma persist directory appends duplicate chunks instead of upserting. Fix: check `db._collection.count()` before re-ingesting, or pass deterministic `ids` (e.g. a hash of the chunk content) to `Chroma.from_documents` so re-runs upsert instead of duplicate.
- [ ] **Fix the fragile `CHROMA_PATH`.** `src/sarma/vectorstore/vectorstore.py` uses `"./../../data/chroma_db"`, which only resolves correctly if the code runs from `notebooks/`. Resolve it relative to the package file instead (e.g. `Path(__file__).resolve().parent.parent.parent / "data" / "chroma_db"`), so it doesn't silently break from `main.py` or a future API entrypoint.
- [ ] **Fix or remove `main.py`.** It imports `from config import OPENAI_API_KEY`, but no `config.py` exists in the repo — running it currently fails. Either wire it to `python-dotenv` (already a dependency) and load from `.env`, or remove it.
- [ ] **Fix or remove `test_ingestion.py`.** It points at `data/raw/example.pdf`, which doesn't exist — real files are under `data/knowledge_base/`. Update the path or delete the test.

## Tier 2 — Graph improvement

- [x] **Conditional retrieval-confidence edge.** `retrieve_node` now returns a similarity score; `route_by_relevance` routes to `generate` only if the best match clears `DEFAULT_SCORE_THRESHOLD` (in `nodes.py`), otherwise to a `no_context` node that returns an explicit refusal without calling the LLM. Remaining: the threshold (`0.5`) is a placeholder — run `notebooks/05_retrieval_eval.ipynb` and tune it against real score distributions.

## Tier 3 — Documentation

- [x] **`docs/architecture.md`** — pipeline diagram, component table, and the two-implementations (chain vs. graph) explanation.
- [x] **`docs/decisions.md`** — first-draft decision log covering the local stack, LangGraph vs. chain, confidence routing, chunking, and citation handling. Written from what the code currently does — review it and adjust the reasoning to match your actual thinking where it doesn't. Entries marked `[confirm/replace]` need the most input.
- [x] **This file** — kept up to date as items complete.

## Tier 4 — Nice to have

- [x] **Retrieval evaluation.** `notebooks/05_retrieval_eval.ipynb` — recall@k against two known-correct Q&A pairs, a score-distribution check to help pick the Tier 2 threshold, and an end-to-end routing check against the compiled graph (including two out-of-domain cases that should be refused). Needs a live Chroma DB and Ollama to run.
- [x] **Guardrail node.** `src/sarma/graph/guardrails.py` — a working input guardrail (pattern-based prompt-injection screening) with instructions in the module docstring for wiring it into `workflow.py`. Left as opt-in for now.
- [x] **README polish.** Added a "how it works" diagram and two verified example Q&A transcripts.

## Out of scope for now

- Expanding the knowledge base with more documents.
- Deploying to cloud / swapping to a hosted LLM API — worth planning as a next step, not building yet.
- Any further architectural refactor beyond the Tier 2 conditional edge — the current structure (ingestion / embeddings / vectorstore / retriever / prompts / llm / graph) is clean and fine to leave as-is.
