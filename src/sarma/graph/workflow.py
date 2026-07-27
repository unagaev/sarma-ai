from functools import partial
from langgraph.graph import StateGraph, START, END

from sarma.graph.state import SarmaState
from sarma.graph.nodes import (
    retrieve_node,
    generate_node,
    no_context_node,
    route_by_relevance,
    DEFAULT_SCORE_THRESHOLD,
)


def create_sarma_graph(retriever, prompt, llm, score_threshold=DEFAULT_SCORE_THRESHOLD):
    """
    retrieve -> [conditional] -> generate -> END
                              -> no_context -> END

    The branch after `retrieve` is the one piece of this graph that a plain
    LangChain chain (see sarma.rag.rag.create_rag_chain) can't express as
    cleanly: retrieval confidence decides whether generation happens at all.
    """

    graph = StateGraph(SarmaState)

    graph.add_node("retrieve", partial(retrieve_node, retriever=retriever, score_threshold=score_threshold))
    graph.add_node("generate", partial(generate_node, prompt=prompt, llm=llm))
    graph.add_node("no_context", no_context_node)

    graph.add_edge(START, "retrieve")
    graph.add_conditional_edges(
        "retrieve",
        route_by_relevance,
        {"generate": "generate", "no_context": "no_context"},
    )
    graph.add_edge("generate", END)
    graph.add_edge("no_context", END)

    return graph.compile()