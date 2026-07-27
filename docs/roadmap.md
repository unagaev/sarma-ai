# SARMA — Roadmap / Pre-Interview Checklist

Status snapshot (as reviewed): ingestion → embeddings → Chroma → retriever → LangGraph (`retrieve` → `generate`) runs end to end and produces correct, cited answers against the agronomy and Sentinel-2 PDFs. The core is done. What's below is tightening, not building from scratch.

Priority order: work top to bottom. Tier 1 first, always — a visible bug undermines everything else you say about the project.

## Tier 1 — Fix before anything else (~1 hour total)

- [ ] **Deduplicate vector store ingestion.** `notebooks/03_semantic_search.ipynb` shows every similarity-search result returned twice with identical scores — re-running ingestion into the same Chroma persist directory appends duplicate chunks instead of upserting. Fix: check `db._collection.count()` before re-ingesting, or pass deterministic `ids` (e.g. a hash of the chunk content) to `Chroma.from_documents` so re-runs upsert instead of duplicate. Worth fixing *and* remembering — "idempotent ingestion" is a real production lesson to cite.
- [ ] **Fix the fragile `CHROMA_PATH`.** `src/sarma/vectorstore/vectorstore.py` uses `"./../../data/chroma_db"`, which only resolves correctly if the code runs from `notebooks/`. Resolve it relative to the package file instead (e.g. `Path(__file__).resolve().parent.parent.parent / "data" / "chroma_db"`), so it doesn't silently break from `main.py` or a future API entrypoint.
- [ ] **Fix or remove `main.py`.** It imports `from config import OPENAI_API_KEY`, but no `config.py` exists in the repo — running it currently fails. Either wire it to `python-dotenv` (already a dependency) and load from `.env`, or delete it so it's not a live embarrassment if someone runs `python main.py`.
- [ ] **Fix or remove `test_ingestion.py`.** It points at `data/raw/example.pdf`, which doesn't exist — your real files are under `data/knowledge_base/`. Update the path or delete the test. A failing test in a repo you might show off is an easy, avoidable red flag.

## Tier 2 — One high-value LangGraph addition (~45 min, optional but recommended)

- [x] **Add one conditional edge.** Done — `retrieve_node` now returns a similarity score; `route_by_relevance` routes to `generate` only if the best match clears `DEFAULT_SCORE_THRESHOLD` (in `nodes.py`), otherwise to a new `no_context` node that refuses without calling the LLM. **Action still needed from you:** the threshold (`0.5`) is a placeholder — run `notebooks/05_retrieval_eval.ipynb` and tune it against real score distributions before relying on this in a demo.

## Tier 3 — Documentation / narrative (~1–2 hours, doubles as interview prep)

- [x] **Fill in `docs/architecture.md`.** Done — pipeline diagram, component table, and the "two implementations" explanation are in there. Re-read it once before the interview so it's in your own words when you say it out loud.
- [x] **Fill in `docs/decisions.md`.** Done as a **first draft** — five ADRs (local stack, LangGraph vs. chain, confidence routing, chunking, citation handling), each with a "what I'd say in the interview" line. **Important:** these are written from what the code does, not your actual original reasoning — go through it and edit the "Why" sections into your real words before the interview. Entries marked `[confirm/replace]` are guesses at your reasoning that need your input most.
- [x] **This file.** Being updated as items complete.

## Tier 4 — Nice-to-have, only if Tiers 1–3 are done with time to spare

- [x] **A minimal retrieval eval.** Done — `notebooks/05_retrieval_eval.ipynb`. Recall@k against the two real, already-verified Q&A pairs from notebook 04, a score-distribution check to help pick the Tier 2 threshold, and an end-to-end routing check against the compiled graph (including two out-of-domain "should refuse" questions). **Run it** — it needs your live Chroma DB and Ollama, which I don't have access to, so it hasn't been executed yet.
- [x] **A guardrail node.** Done, but **deliberately not wired into the default graph** — `src/sarma/graph/guardrails.py` has a working `guard_node` + router (pattern-based prompt-injection screening) and instructions in the module docstring for adding it to `workflow.py` if you want it. Left as opt-in so Tier 2's change stays the one thing you need to have fully tested and understood.
- [x] **README polish.** Done — added a "How it works" diagram and the two real, verified example Q&A transcripts from notebook 04.

## Explicitly not worth your remaining days

- Expanding the knowledge base with more documents — breadth doesn't change what this interview is testing.
- Deploying to cloud / swapping to a hosted LLM API — a good thing to *discuss* as a next step, not to *build* this week.
- Any further architectural refactor beyond the one conditional edge in Tier 2 — the current structure (ingestion / embeddings / vectorstore / retriever / prompts / llm / graph) is already clean and is a fine thing to leave as-is.
