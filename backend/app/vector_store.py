import faiss
import numpy as np
from sentence_transformers import SentenceTransformer


# Embedding model
model = SentenceTransformer("all-MiniLM-L6-v2")


class VectorStore:

    def __init__(self):
        # all-MiniLM-L6-v2 produces 384-dimensional embeddings
        self.index = faiss.IndexFlatL2(384)

        # Stores the original document chunks
        self.chunks = []

    # -----------------------------------------
    # Add document chunks
    # -----------------------------------------
    def add_chunks(self, chunks):

        if not chunks:
            return

        texts = [
            chunk["text"]
            for chunk in chunks
            if chunk.get("text")
        ]

        if not texts:
            return

        embeddings = model.encode(
            texts,
            convert_to_numpy=True
        )

        embeddings = np.asarray(
            embeddings,
            dtype="float32"
        )

        self.index.add(embeddings)

        self.chunks.extend(
            [
                chunk
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

        # No documents indexed
        if not self.chunks:
            return []

        query_embedding = model.encode(
            [query],
            convert_to_numpy=True
        )

        query_embedding = np.asarray(
            query_embedding,
            dtype="float32"
        )

        # Don't ask FAISS for more items than exist
        search_k = min(k, len(self.chunks))

        distances, indices = self.index.search(
            query_embedding,
            search_k
        )

        results = []

        for distance, idx in zip(
            distances[0],
            indices[0]
        ):

            if idx < 0 or idx >= len(self.chunks):
                continue

            # Ignore weak semantic matches
            if float(distance) > max_distance:
                continue

            chunk = dict(self.chunks[idx])

            # Useful for debugging and ranking
            chunk["distance"] = float(distance)

            results.append(chunk)

        return results


# Global vector store
vector_store = VectorStore()