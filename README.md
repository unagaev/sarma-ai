# SARMA AI

Geospatial Environmental Intelligence Assistant that combines Retrieval-Augmented Generation (RAG), AI agents, and spatial analytics to help users explore environmental documents, satellite information, and geospatial datasets through natural language.

## Features

- RAG
- LangGraph
- LangChain
- Ollama
- BGE Embeddings
- Chroma
- Python

## How it works

```
PDF documents  ─▶  loader (per-page metadata: source, page)
               ─▶  splitter (RecursiveCharacterTextSplitter, 1000 chars / 200 overlap)
               ─▶  BGE embeddings (BAAI/bge-small-en-v1.5, local via HuggingFace)
               ─▶  Chroma vector store (local, persisted to data/chroma_db)

question  ─▶  retrieve (similarity search + score)
          ─▶  [conditional: is the best match similar enough to trust?]
                 ├─ yes ─▶ generate (Ollama, grounded in retrieved context) ─▶ answer + citations
                 └─ no  ─▶ no_context ─▶ explicit "I don't have enough information"
```

The pipeline is implemented as a [LangGraph](https://github.com/langchain-ai/langgraph) `StateGraph` (`src/sarma/graph/`) so retrieval confidence can route the request rather than always forcing a generation step — see `docs/architecture.md` and `docs/decisions.md` for the reasoning. A simpler, linear-chain version of the same pipeline (`SarmaAssistant` / `create_rag_chain`) also exists in the codebase as a point of comparison.

Everything currently runs fully local (Ollama for generation, BGE for embeddings, Chroma for storage) — no document content or query ever leaves the machine it runs on.

## Example

```
Q: What are the recommended nitrogen rates for spring wheat?

A: The recommended nitrogen rates for spring-sown wheat, based on soil type
   and SNS Index, are as follows:
   - Light sand soils: SNS Index 0: 160 kg N/ha ... SNS Index 6: 0 kg N/ha
   - All other mineral soils: SNS Index 0: 210a kg N/ha ... (210a exceeds the
     N max limit in Nitrate Vulnerable Zones)
   ...

Sources:
- RB209 Arable crops.pdf, page 32
```

```
Q: What is Sentinel-2?

A: Sentinel-2 is a European Earth polar-orbiting satellite constellation
   consisting of two identical satellites (Sentinel-2A and 2B) that operate
   on a single orbit plane with a 180º phase difference. Each satellite
   hosts a Multi-Spectral Instrument (MSI) capable of capturing
   high-resolution imagery across the visible to shortwave infrared
   spectral range...

Sources:
- Sentinel-2-product-specifications-document-V14-9.pdf, page 39
- Sentinel-2-product-specifications-document-V14-9.pdf, page 26
- Sentinel-2-product-specifications-document-V14-9.pdf, page 23
```

See `notebooks/04_assistant_test.ipynb` for the full runs, and `notebooks/05_retrieval_eval.ipynb` for a small recall@k / routing evaluation.

## Status

Under active development. Core RAG pipeline (ingestion → embeddings → retrieval → grounded generation with citations) is working end-to-end via both a LangChain chain and a LangGraph state graph with confidence-based routing. See `docs/roadmap.md` for what's next.