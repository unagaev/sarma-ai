# SARMA

Geospatial Environmental Intelligence Assistant — a local Retrieval-Augmented Generation (RAG) system over environmental PDF documents, merged with a live geospatial analysis branch (satellite land cover + vegetation index) into a single grounded answer.

## What it does

Given a natural-language question, SARMA runs two independent analyses in parallel and merges both into one LLM-generated answer:

- **Document retrieval (RAG):** semantic search over a local Chroma vector store built from PDF documents (currently a UK agronomy nutrient-management guide and the Sentinel-2 product specification), returning cited passages.
- **GIS analysis:** land cover classification (ESA WorldCover) and vegetation index (NDVI, from live Sentinel-2 imagery) for a fixed area of interest.

The LLM is instructed to treat GIS output as observed measurement and document content as supporting explanation/interpretation — not to blend or invent either.

Everything runs locally: Ollama for generation (`qwen3:8b`), BGE for embeddings, Chroma for vector storage. No document content or question leaves the machine. Satellite imagery and land-cover tiles are fetched from public AWS-hosted sources (Earth Search STAC, ESA WorldCover).

**Current scope:** the area of interest and the Sentinel-2 date range are fixed in code, not derived from the user's question — every query analyses the same location.

## How it works

```
PART 1 — build the index (offline)
  PDF corpus ──▶ loader (per-page metadata) ──▶ splitter (1000/200 chars)
             ──▶ BGE embeddings (local) ──▶ Chroma vector store (persisted)

PART 2 — answer a question (online, via a LangGraph StateGraph)

  question
     │
     ├──▶ GIS branch: load AOI ─▶ land cover (WorldCover) ─▶ Sentinel-2 imagery
     │                ─▶ NDVI ─▶ gis_data
     │
     └──▶ RAG branch: embed question ─▶ similarity search (+ score) ─▶ documents
                                                                          │
     gis_data + documents ─────────────────────────────────────────────▶┤
                                                                          ▼
                                                                 LLM generation
                                                            (grounded in both inputs)
                                                                          │
                                                                          ▼
                                                            answer + citations
```

The pipeline is implemented as a [LangGraph](https://github.com/langchain-ai/langgraph) `StateGraph` (`src/sarma/graph/`), which runs the GIS and retrieval branches from `START` and joins them before generation. See `docs/architecture.md` and `docs/decisions.md` for background — note both currently describe an earlier, RAG-only version of the graph and need updating to reflect the GIS branch (see Status below).

## Project structure

| Path | Responsibility |
|---|---|
| `src/sarma/ingestion/loader.py` | `load_pdf()` — loads one PDF, tags each page with `source`/`page` metadata. |
| `src/sarma/ingestion/knowledge_base.py` | `load_knowledge_base()` — loads every PDF under `data/knowledge_base/`. |
| `src/sarma/ingestion/splitter.py` | `split_documents()` — chunks documents (1000 chars / 200 overlap), preserving metadata. |
| `src/sarma/embeddings.py` | The embedding model: `BAAI/bge-small-en-v1.5`, local via `langchain_huggingface`. |
| `src/sarma/vectorstore/vectorstore.py` | `create_vector_store()` / `load_vector_store()` — builds/reloads the local Chroma collection at `data/chroma_db`. |
| `src/sarma/retriever.py` | `create_retriever()` — wraps the vector store as a retriever (`k=5`). |
| `src/sarma/prompts.py` | `rag_prompt` — the generation prompt; expects `gis_data`, `context`, and `question`. |
| `src/sarma/llm.py` | The generation model: `ChatOllama(model="qwen3:8b", temperature=0)`, local. |
| `src/sarma/citations.py` | `format_citations()` — deduplicated `"source, page N"` list from retrieved documents. |
| `src/sarma/tools/sentinel.py` | Sentinel-2 STAC search, band loading, cloud-free mosaic (`search_sentinel2`, `load_sentinel2`, `create_mosaic`), plus `load_aoi()`. |
| `src/sarma/tools/worldcover.py` | ESA WorldCover tile download, clip to AOI, land-cover percentages (`download_tiles`, `clip_to_aoi`, `landcover_statistics`). |
| `src/sarma/tools/ndvi.py` | `calculate_ndvi()` / `ndvi_statistics()` — vegetation index from red/NIR bands. |
| `src/sarma/tools/analysis.py` | `analyse_area()` — orchestrates the three modules above into one GIS result. |
| `src/sarma/graph/state.py` | `SarmaState` — the shared state passed between graph nodes. |
| `src/sarma/graph/nodes.py` | Node functions: `retrieve_node`, `generate_node`, `gis_node`, `no_context_node`, `route_by_relevance`. |
| `src/sarma/graph/workflow.py` | `create_sarma_graph()` — assembles the nodes into the compiled graph described above. |
| `src/sarma/graph/guardrails.py` | An optional, **not wired in** input-screening node (pattern-based prompt-injection checks) — see its docstring to enable it. |

## Setup

```
pip install -e .
```

`requirements.txt` in this repo is a full environment export from a Windows/conda setup (includes local build paths) — treat it as a reference, not a portable install file. `pyproject.toml` lists the actual package; a clean environment plus the imports used in `src/sarma/` (LangChain, LangGraph, `langchain-huggingface`, `langchain-chroma`, `langchain-ollama`, `geopandas`, `pystac-client`, `odc-stac`, `odc-geo`, `rasterio`, `shapely`, `requests`) is enough to run it.

Also required: [Ollama](https://ollama.com) running locally with `qwen3:8b` pulled (`ollama pull qwen3:8b`).

## Usage

```python
from sarma.vectorstore.vectorstore import load_vector_store
from sarma.retriever import create_retriever
from sarma.graph.workflow import create_sarma_graph
from sarma.prompts import rag_prompt
from sarma.llm import llm

retriever = create_retriever(load_vector_store())
graph = create_sarma_graph(retriever, rag_prompt, llm)

result = graph.invoke({"question": "How healthy is the vegetation in this area?"})
print(result["answer"])
print(result["citations"])
print(result["gis_data"])
```

See `notebooks/04_assistant_test.ipynb` for full runs and `notebooks/06_sentinel_ndvi_test.ipynb` for a standalone Sentinel-2 → NDVI test. A real run against the current fixed AOI returned land cover of roughly 51.5% grassland, 33.5% permanent water, 14% tree cover, and a mean NDVI of 0.51.

## Status

Core pipeline (ingestion → embeddings → retrieval, and GIS analysis → NDVI/land cover) both run end-to-end and merge into one grounded, cited answer via the LangGraph implementation. Known gaps, in rough priority order:

- **Retrieval confidence gate is currently disabled.** `route_by_relevance()` in `graph/nodes.py` is hardcoded to always proceed to generation instead of routing on `sufficient_context`; a question with no relevant documents will still get an answer instead of an explicit refusal.
- **GIS analysis re-runs on every question**, with no caching, even though the AOI and date range never change between calls — `analyse_area()` re-downloads/re-computes everything each time.
- **Vector store ingestion is not idempotent** — re-running ingestion into the same Chroma directory appends duplicate chunks rather than upserting.
- **`tools/worldcover.py` has a hardcoded, machine-specific path** (`BASE_DIR`), so it only runs as-is on the original development machine.
- `docs/architecture.md`, `docs/decisions.md`, and `docs/roadmap.md` describe an earlier, RAG-only version of the graph and need updating to reflect the GIS branch and the points above.

## Knowledge base

`data/knowledge_base/` is organised by topic (`agronomy/`, `climate/`, `papers/`, `remote_sensing/`, `soil/`); only `agronomy/` and `remote_sensing/` currently contain documents.
