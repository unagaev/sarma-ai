# SARMA — Decisions

> **This is a first draft**, written from what the code actually does, not from a record of the reasoning as it happened. Read each entry and edit the "Why" / "Tradeoffs" sections into your own words and your own real reasons before the interview — an interviewer probing "why did you choose X" wants *your* judgment, and it should sound like you thinking, not like a document. Where I wasn't sure of your actual reason, I've marked it `[confirm/replace]`.

---

## ADR-1: Fully local stack (Ollama + BGE + Chroma) instead of hosted APIs

**Decision:** Run generation (Ollama, `qwen3:8b`), embeddings (BGE via HuggingFace), and vector storage (Chroma) entirely locally, with no calls to OpenAI/Anthropic/a hosted vector DB.

**Why:** `[confirm/replace — likely some mix of:]` no API cost while iterating during development; no need to manage API keys/quotas for a personal project; a legitimate architecture pattern for clients who can't send document content to a third-party API (data residency / confidentiality — relevant for an energy/utility/regulated client, not just this project).

**Tradeoffs:** Generation latency is high on local hardware — observed ~23–57s per answer in `notebooks/04_assistant_test.ipynb` (CPU-bound `qwen3:8b` generation). That's fine for development and for a demo where you narrate it, but not acceptable for a production/user-facing tool. In production this would move to either a hosted API (AWS Bedrock / Azure OpenAI / GCP Vertex AI) for latency, or a locally-hosted model behind a proper inference server (vLLM, TGI) with GPU acceleration, keeping the "data stays local" property while fixing the latency.

**What I'd say in the interview:** "I built this against a fully local stack — partly for cost and iteration speed during development, but it's also a real architecture pattern: for a client that can't send data to a third-party API, this is the shape the solution takes. The tradeoff is latency, which I'd solve in production with [a GPU-backed local inference server / a private hosted endpoint within the client's cloud boundary], not by giving up the data-locality property."

---

## ADR-2: LangGraph `StateGraph` alongside a plain LangChain chain

**Decision:** Implement the same retrieve→generate pipeline twice — once as a simple LCEL chain (`create_rag_chain`) / class (`SarmaAssistant`), and once as a LangGraph `StateGraph` (`create_sarma_graph`).

**Why:** `[confirm/replace]` Started with the chain as the simplest thing that could work. Moved to LangGraph once the pipeline needed to *branch* (retrieval-confidence routing — added for the interview prep, see ADR-3) rather than always run linearly start to finish — that's a state-graph-shaped problem, not a chain-shaped one.

**Tradeoffs:** At the current scope (one conditional branch), LangGraph isn't doing dramatically more than a chain with an if-statement wrapped around it could do. The honest justification is forward-looking: the natural next additions (an input guardrail node, a reranking node, a human-approval step before a high-stakes recommendation, a multi-step "clarify then retrieve" loop) are all graph-shaped, and having the `StateGraph` foundation in place means adding them is additive (`add_node` + `add_edge`) rather than a rewrite.

**What I'd say in the interview:** "For a simple linear pipeline, LangGraph and a chain are close to equivalent — I wouldn't claim otherwise if asked directly. I chose the graph because the moment you need conditional routing, human-in-the-loop steps, or multi-agent hand-off, a chain doesn't model that cleanly and a graph does. I built the foundation now so those additions are structural, not rewrites."

---

## ADR-3: Confidence-based routing before generation (added for Tier 2)

**Decision:** `retrieve_node` now returns a similarity score alongside documents; a conditional edge routes to `generate` only if the best match is below a distance threshold, otherwise to `no_context`, which returns an explicit refusal without calling the LLM.

**Why:** The prompt already asks the LLM to say "I don't have enough information" when the context doesn't answer the question — but that relies on the LLM reliably following the instruction every time, on every model, under every context. Enforcing it structurally (before the LLM is even called) is more reliable and cheaper (skips a ~20-50s local generation call entirely for questions the knowledge base can't answer).

**Tradeoffs:** The threshold (`DEFAULT_SCORE_THRESHOLD = 0.5` in `nodes.py`) is currently a starting guess, not a validated value — Chroma's default distance metric means lower scores are more similar, and the right cut point depends on the actual score distribution for in-domain vs. out-of-domain questions in this specific corpus and embedding model. `notebooks/05_retrieval_eval.ipynb` exists to measure that distribution and pick a real value before relying on this in an interview demo.

**What I'd say in the interview:** "I didn't want to trust the prompt alone to enforce grounding, so I moved the check into the graph itself — if retrieval isn't confident, we never call the LLM at all. The threshold needs tuning against real score distributions, which is exactly what the eval notebook does; I'd treat shipping an untuned threshold to production the same way I'd treat shipping an unvalidated classification cutoff — as a placeholder, not a decision."

---

## ADR-4: Chunking at 1000 characters / 200 overlap

**Decision:** `RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)`.

**Why:** `[confirm/replace]` A reasonable default for dense technical/reference documents (regulatory tables, satellite spec sheets) where a chunk needs enough surrounding text to be meaningful on its own, without being so large that irrelevant content dilutes the embedding.

**Tradeoffs:** Not yet validated against alternatives. A natural Tier-4-and-beyond experiment: re-run `05_retrieval_eval.ipynb`'s recall@k at a couple of different chunk sizes (e.g. 500/100 and 1500/300) and see whether recall actually improves — right now 1000/200 is a sensible default, not a measured optimum.

**What I'd say in the interview:** "I picked a standard mid-size chunk with meaningful overlap as a sensible starting point, and I have an eval harness that would let me actually test whether a different size retrieves better — I haven't run that sweep yet, but I know exactly how I'd do it."

---

## ADR-5: Citations carried through metadata, not re-derived

**Decision:** Source filename and page number are attached to every document at ingestion time (`loader.py`) and simply passed through chunking, retrieval, and into the final citation list (`citations.py`) — never re-parsed or re-inferred later.

**Why:** Citation accuracy has to be a data-pipeline guarantee, not a generation-time hope. If citations were extracted from the LLM's output text instead, they'd be exactly as reliable as the LLM's ability to remember and correctly format a page number — which is a hallucination risk for no good reason, since the real page number is already known and exact at ingestion time.

**Tradeoffs:** None significant — this is close to strictly better than the alternative. Worth stating in the interview as a deliberate design principle, not an accident: "ground truth metadata flows through the pipeline; nothing downstream is asked to reconstruct it."
