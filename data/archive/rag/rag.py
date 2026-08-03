from langchain_core.runnables import RunnablePassthrough

from sarma.llm import llm
from sarma.prompts import rag_prompt

def create_rag_chain(retriever):
    
    chain = ({"context": retriever, "question": RunnablePassthrough()} | rag_prompt | llm)
    
    return chain