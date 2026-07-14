def create_retriever(vector_db):

    return vector_db.as_retriever(
        search_kwargs={"k": 10}
    )