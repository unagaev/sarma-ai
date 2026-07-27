"""
Optional input guardrail node (Tier 4 - not wired into create_sarma_graph by
default). Either way,
it's a legitimate thing to describe as "designed but deliberately not
rushed into the graph without testing."

To wire it in, in workflow.py:

    from sarma.graph.guardrails import guard_node, route_after_guard

    graph.add_node("guard", guard_node)
    graph.add_edge(START, "guard")
    graph.add_conditional_edges("guard", route_after_guard, {"retrieve": "retrieve", "blocked": "blocked"})
    graph.add_node("blocked", blocked_node)
    graph.add_edge("blocked", END)
    # and change the old `graph.add_edge(START, "retrieve")` to start at "guard" instead.

Also add "blocked: Optional[bool]" to SarmaState if you wire this in, so the
router has something to read.
"""

import re

# Deliberately simple, pattern-based checks - not a claim that this is a
# complete prompt-injection defence, just a first line of screening before
# a question reaches retrieval/generation. Extend this list as you find
# real cases worth blocking.
BLOCKLIST_PATTERNS = [
    r"ignore (all|previous|the) instructions",
    r"disregard (all|previous|the) (instructions|rules)",
    r"system prompt",
    r"reveal your (prompt|instructions)",
    r"you are now",  # common jailbreak/role-override phrasing
]


def guard_node(state):
    """
    Screens the incoming question before it reaches retrieval or the LLM.
    """

    question = state["question"]

    for pattern in BLOCKLIST_PATTERNS:
        if re.search(pattern, question, re.IGNORECASE):
            return {"blocked": True}

    return {"blocked": False}


def blocked_node(state):
    return {
        "context": "",
        "answer": "This question couldn't be processed.",
        "citations": [],
    }


def route_after_guard(state):
    return "blocked" if state.get("blocked") else "retrieve"
