def format_citations(documents):

    citations = []

    for doc in documents:

        source = doc.metadata.get(
            "source",
            "Unknown"
        )

        page = doc.metadata.get(
            "page",
            "Unknown"
        )

        citations.append(
            f"{source}, page {page}"
        )

    return list(set(citations))