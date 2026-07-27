# SARMA — Decisions

> **First draft**, written from what the code currently does rather than a record of the reasoning as it happened. Review each entry and adjust the "Why" / "Tradeoffs" sections to match your actual reasoning — a decisions log should read as your own judgment, not an inferred description of it. Entries marked `[confirm/replace]` are the least certain and need the most input.

---

## ADR-1: Fully local stack (Ollama + BGE + Chroma) instead of hosted APIs

**Decision:** Run generation (Ollama, `qwen3:8b`), embeddings (BGE via HuggingFace), and vector storage (Chroma) entirely locally, with no calls to OpenAI/Anthropic/a hosted vector DB.

**Why:** `[confirm/replace — likely some mix of:]` no API cost while iterating during development; no need to manage API keys/quotas; a legitimate architecture pattern for use cases where document content can't leave the local environment (data residency / confidentiality constraints, relevant beyond this project).

**Tradeoffs:** Generation latency is high on local hardware — observed ~23–57s per answer in `notebooks/04_assistant_test.ipynb` (CPU-bound `qwen3:8b` generation). Fine for development; not acceptable for a production/user-facing tool as-is. Moving to production would mean either a hosted API (AWS Bedrock / Azure OpenAI / GCP Vertex AI) for latency, or a locally-hosted model behind a proper inference server (vLLM, TGI) with GPU acceleration, preserving the data-locality property while fixing the latency.

---

## ADR-2: LangGraph `StateGraph` alongside a plain LangChain chain

**Decision:** Implement the same retrieve→generate pipeline twice — once as a simple LCEL chain (`create_rag_chain`) / class (`SarmaAssistant`), and once as a LangGraph `StateGraph` (`create_sarma_graph`).

**Why:** `[confirm/replace]` Started with the chain as the simplest thing that could work. Moved to LangGraph once the pipeline needed to *branch* (retrieval-confidence routing, see ADR-3) rather than always run linearly start to finish — that's a state-graph-shaped problem, not a chain-shaped one.

**Tradeoffs:** At the current scope (one conditional branch), LangGraph isn't doing dramatically more than a chain with an if-statement wrapped around it could do. The justification is forward-looking: natural next additions (an input guardrail node, a reranking node, a human-approval step before a high-stakes recommendation, a multi-step "clarify then retrieve" loop) are all graph-shaped, and having the `StateGraph` foundation in place means adding them is additive (`add_node` + `add_edge`) rather than a rewrite.

---

## ADR-3: Confidence-based routing before generation

**Decision:** `retrieve_node` returns a similarity score alongside documents; a conditional edge routes to `generate` only if the best match is below a distance threshold, otherwise to `no_context`, which returns an explicit refusal without calling the LLM.

**Why:** The prompt already asks the LLM to say "I don't have enough information" when the context doesn't answer the question — but that relies on the LLM reliably following the instruction every time, on every model, under every context. Enforcing it structurally (before the LLM is even called) is more reliable and cheaper (skips a ~20–50s local generation call entirely for questions the knowledge base can't answer).

**Tradeoffs:** The threshold (`DEFAULT_SCORE_THRESHOLD = 0.5` in `nodes.py`) is currently a starting guess, not a validated value — Chroma's default distance metric means lower scores are more similar, and the right cut point depends on the actual score distribution for in-domain vs. out-of-domain questions in this specific corpus and embedding model. `notebooks/05_retrieval_eval.ipynb` exists to measure that distribution and pick a real value; treat the current default as a placeholder, not a finished decision.

---

## ADR-4: Chunking at 1000 characters / 200 overlap

**Decision:** `RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)`.

**Why:** `[confirm/replace]` A reasonable default for dense technical/reference documents (regulatory tables, satellite spec sheets) where a chunk needs enough surrounding text to be meaningful on its own, without being so large that irrelevant content dilutes the embedding.

**Tradeoffs:** Not yet validated against alternatives. A natural follow-up experiment: re-run `05_retrieval_eval.ipynb`'s recall@k at a couple of different chunk sizes (e.g. 500/100 and 1500/300) and see whether recall actually improves — right now 1000/200 is a sensible default, not a measured optimum.

---

## ADR-5: Citations carried through metadata, not re-derived

**Decision:** Source filename and page number are attached to every document at ingestion time (`loader.py`) and passed through chunking, retrieval, and into the final citation list (`citations.py`) — never re-parsed or re-inferred later.

**Why:** Citation accuracy has to be a data-pipeline guarantee, not a generation-time hope. If citations were extracted from the LLM's output text instead, they'd be exactly as reliable as the LLM's ability to remember and correctly format a page number — an unnecessary hallucination risk, since the real page number is already known and exact at ingestion time.

**Tradeoffs:** None significant — this is close to strictly better than the alternative. A deliberate design principle: ground-truth metadata flows through the pipeline; nothing downstream is asked to reconstruct it.
