from pathlib import Path
from sarma.ingestion.loader import load_pdf

def load_knowledge_base(data_dir: str):
    data_path = Path(data_dir)
    if not data_path.exists():
        raise FileNotFoundError(f"{data_dir} does not exist")
    
    documents = []
    pdf_files = sorted(data_path.rglob("*.pdf"))
    if not pdf_files:
        raise ValueError(f"No PDF files found in {data_dir}")
   
    print(f"found {len(pdf_files)} PDF(s)\n")
    
    for pdf in pdf_files:
        print(f"Loaing {pdf.name}")
        docs = load_pdf(str(pdf))
        documents.extend(docs)
    print(f"\nLoaded {len(documents)} pages.")
    return documents