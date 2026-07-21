from pathlib import Path

from langchain_community.document_loaders import PyPDFLoader


def load_pdf(file_path: str):
    """
    Load PDF and preserve citation metadata.
    """

    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(
            f"File not found: {file_path}"
        )

    loader = PyPDFLoader(str(path))

    documents = loader.load()

    for doc in documents:

        doc.metadata["source"] = path.name

        # LangChain uses zero-based pages
        # Convert to human page numbering
        if "page" in doc.metadata:
            doc.metadata["page"] += 1

    return documents