import math
import re
from collections import Counter


class VectorStore:

    def __init__(self):
        self.chunks = []

    # -----------------------------------------
    # Add document chunks
    # -----------------------------------------
    def add_chunks(self, chunks):

        if not chunks:
            return

        self.chunks.extend(
            [
                dict(chunk)
                for chunk in chunks
                if chunk.get("text")
            ]
        )

    # -----------------------------------------
    # Search document
    # -----------------------------------------
    def search(
        self,
        query,
        k=5,
        max_distance=1.80
    ):

        if not self.chunks:
            return []

        query_terms = Counter(re.findall(r"\w+", query.lower()))
        if not query_terms:
            return []

        document_terms = [
            Counter(re.findall(r"\w+", chunk["text"].lower()))
            for chunk in self.chunks
        ]
        document_count = len(document_terms)
        average_length = sum(
            sum(terms.values()) for terms in document_terms
        ) / document_count
        document_frequencies = Counter(
            term
            for terms in document_terms
            for term in terms
        )

        ranked_chunks = []
        for index, (chunk, terms) in enumerate(
            zip(self.chunks, document_terms)
        ):
            document_length = sum(terms.values())
            score = 0.0

            for term, query_frequency in query_terms.items():
                term_frequency = terms.get(term, 0)
                if not term_frequency:
                    continue

                document_frequency = document_frequencies[term]
                inverse_frequency = math.log(
                    1 + (document_count - document_frequency + 0.5)
                    / (document_frequency + 0.5)
                )
                length_normalization = (
                    1 - 0.75 + 0.75 * document_length / average_length
                )
                score += (
                    inverse_frequency
                    * term_frequency
                    * 2.5
                    / (term_frequency + 1.5 * length_normalization)
                    * query_frequency
                )

            if score <= 0:
                continue

            distance = 1 / (1 + score)
            if distance <= max_distance:
                result = dict(chunk)
                result["distance"] = distance
                ranked_chunks.append((score, index, result))

        ranked_chunks.sort(key=lambda item: (-item[0], item[1]))
        return [
            item[2]
            for item in ranked_chunks[:max(0, k)]
        ]


# Global vector store
vector_store = VectorStore()