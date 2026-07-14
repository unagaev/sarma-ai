from langchain_ollama import ChatOllama

llm = ChatOllama(model="qwen3:8b", temperature=0, extra_body={
        "think": False
    })