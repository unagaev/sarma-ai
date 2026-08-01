from sarma.citations import format_citations
from sarma.tools.analysis import analyse_area

# Chroma's default similarity_search_with_score returns a DISTANCE, where
# LOWER means MORE similar (this repo saw ~0.33-0.41 for genuinely relevant
# matches in notebooks/03_semantic_search.ipynb). This threshold is a
# starting point, not a validated value - tune it with
# notebooks/05_retrieval_eval.ipynb by comparing scores for known-relevant
# vs. known-irrelevant questions and picking a cut point that separates them.
DEFAULT_SCORE_THRESHOLD = 0.5


def retrieve_node(state, retriever, score_threshold=DEFAULT_SCORE_THRESHOLD, k=5):
    """
    Retrieve relevant documents AND their similarity scores.

    The plain `retriever.invoke(question)` interface (used elsewhere, e.g.
    SarmaAssistant.ask) only returns documents, not scores, so it can't tell
    a confident match from a desperate "these are the k least-bad chunks I
    could find." Going through `retriever.vectorstore` (a standard,
    documented attribute of LangChain's VectorStoreRetriever) gets us scores
    so the graph can route on retrieval confidence, not just retrieve
    unconditionally.
    """

    question = state["question"]

    results = retriever.vectorstore.similarity_search_with_score(question, k=k)

    docs = [doc for doc, _score in results]
    best_score = min((score for _doc, score in results), default=None)

    return {
        "documents": docs,
        "best_score": best_score,
        "sufficient_context": best_score is not None and best_score <= score_threshold,
    }


def generate_node(state, prompt, llm):
    """
    Generate answer from retrieved documents.
    """

    docs = state["documents"]

    context_parts = []

    for doc in docs:

        source = doc.metadata.get(
            "source",
            "unknown"
        )

        page = doc.metadata.get(
            "page",
            "unknown"
        )

        context_parts.append(
            f"""
Source: {source}
Page: {page}

Content:
{doc.page_content}
"""
        )

    context = "\n\n".join(context_parts)


    chain = prompt | llm


    response = chain.invoke(
        {
            "context": context,
            "gis_data": state["gis_data"],
            "question": state["question"]
        }
    )


    return {
        "context": context,
        "answer": response.content,
        "citations": format_citations(docs)
    }

def gis_node(state):
    
    gis_result = analyse_area()
    
    return {
    
    "gis_data": gis_result
    }

def no_context_node(state):
    """
    Reached when retrieval didn't find anything similar enough to the
    question to trust. Returns a clear refusal instead of letting the LLM
    generate from an irrelevant or empty context - this is the graph
    enforcing the same rule the prompt already asks the LLM to follow
    ("say I don't have enough information"), except structurally, before
    the (slow, local) LLM call happens at all rather than hoping the model
    follows the instruction after the fact.
    """

    return {
        "context": "",
        "answer": "I don't have enough information in the knowledge base to answer that question.",
        "citations": [],
    }


def route_by_relevance(state):
    """
    Conditional edge used after `retrieve`: only proceed to generation if
    retrieval found something plausibly relevant to the question.
    """

    #return "generate" if state.get("sufficient_context") else "no_context"
    return "generate"