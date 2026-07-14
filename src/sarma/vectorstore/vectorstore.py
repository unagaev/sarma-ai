from langchain_chroma import Chroma
from sarma.embeddings import embeddings

def create_vector_store(chunks):
	
    vector_db = Chroma.from_documents(documents=chunks, embedding=embeddings, persist_directory="./chroma_db")
    return vector_db