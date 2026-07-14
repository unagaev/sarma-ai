from langchain_core.prompts import ChatPromptTemplate

rag_prompt = ChatPromptTemplate.from_template(
"""
You are SARMA, a geospatial environmental intelligence assistant.

Answer the question using ONLY the provided context.

If the answer is not in the context, say:
"I don't have enough information."

Context:
{context}

Question:
{question}

Answer:
"""
)