from pathlib import Path
from langchain_chroma import Chroma
from sarma.embeddings import embeddings

CHROMA_PATH = str(Path(__file__).resolve().parent.parent.parent.parent / "data" / "chroma_db")

def create_vector_store(chunks):
	
    vector_db = Chroma.from_documents(documents=chunks, embedding=embeddings, persist_directory=CHROMA_PATH)
    return vector_db

def load_vector_store():
    if not Path(CHROMA_PATH).exists():
        raise FileNotFoundError('Vector database not found')

    return Chroma(persist_directory=CHROMA_PATH, embedding_function=embeddings)