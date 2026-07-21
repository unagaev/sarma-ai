import time

class SarmaAssistant:

    def __init__(self, retriever, prompt, llm):

        self.retriever = retriever
        self.prompt = prompt
        self.llm = llm


    def extract_citations(self, docs):
        """
        Extract unique citations from retrieved documents.
        """

        citations = []

        seen = set()

        for doc in docs:

            source = doc.metadata.get(
                "source",
                "unknown"
            )

            page = doc.metadata.get(
                "page",
                None
            )

            key = (
                source,
                page
            )

            if key not in seen:

                citations.append(
                    {
                        "source": source,
                        "page": page,
                    }
                )

                seen.add(key)

        return citations


    def build_context(self, docs):
        """
        Build LLM context with citation metadata included.
        """

        context_parts = []

        for doc in docs:

            source = doc.metadata.get(
                "source",
                "unknown"
            )

            page = doc.metadata.get(
                "page",
                "unknown"
            )

            context_parts.append(
                f"""
Source: {source}
Page: {page}

Content:
{doc.page_content}
"""
            )

        return "\n\n".join(
            context_parts
        )


    def ask(self, question):

        # -------------------------
        # Retrieval
        # -------------------------

        t0 = time.time()

        docs = self.retriever.invoke(
            question
        )

        print(
            f"Retrieval: {time.time() - t0:.2f} s"
        )


        # -------------------------
        # Prepare context
        # -------------------------

        context = self.build_context(
            docs
        )


        # -------------------------
        # LLM generation
        # -------------------------

        chain = self.prompt | self.llm

        t1 = time.time()

        response = chain.invoke(
            {
                "context": context,
                "question": question,
            }
        )

        print(
            f"LLM: {time.time() - t1:.2f} s"
        )


        # -------------------------
        # Citations
        # -------------------------

        citations = self.extract_citations(
            docs
        )


        # -------------------------
        # Final response
        # -------------------------

        return {
            "question": question,
            "answer": response.content,
            "citations": citations,
            "retrieved_documents": docs,
        }