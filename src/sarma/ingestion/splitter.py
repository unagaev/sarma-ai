from langchain_text_splitters import RecursiveCharacterTextSplitter

def split_documents(documents):
    """
    Split documents into smaller chunks.
    """
    
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1500,
        chunk_overlap=300
        )
        
    chunks = splitter.split_documents(documents)
    
    return chunks