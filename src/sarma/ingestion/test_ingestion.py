from sarma.ingestion.loader import load_pdf
from sarma.ingestion.splitter import split_documents

def test_ingestion_pipeline():
    
    documents = load_pdf("data/raw/example.pdf")
    
    assert len(documents) > 0
    
    chunks = split_documents(documents)
    
    assert len(chunks) > 0
    
    assert "source" in chunks[0].metadata
    assert "page" in chunks[0].metadata
        