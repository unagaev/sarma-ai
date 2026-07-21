def extract_citations(documents):
    """
    Extract citation information from retrieved documents.
    """

    citations = []

    seen = set()

    for doc in documents:

        source = doc.metadata.get(
            "source",
            "unknown"
        )

        page = doc.metadata.get(
            "page",
            None
        )

        citation = {
            "source": source,
            "page": page
        }

        key = (
            source,
            page
        )

        if key not in seen:
            citations.append(citation)
            seen.add(key)

    return citations