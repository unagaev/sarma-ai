from typing import TypedDict, List, Optional

class SarmaState(TypedDict):
    question: str
    documents: list
    context: str
    answer: str
    citations: List[str]
    best_score: Optional[float]        # lowest (= most similar) Chroma distance among retrieved docs
    sufficient_context: Optional[bool]  # set by retrieve_node; drives the conditional edge in workflow.py