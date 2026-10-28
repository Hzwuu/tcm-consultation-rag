from __future__ import annotations

import hashlib
import math
import os
from dataclasses import dataclass
from typing import Protocol

from .models import Record
from .retrieval import keyword_score, tokenize


class EmbeddingProvider(Protocol):
    name: str

    def encode(self, texts: list[str]) -> list[list[float]]:
        """Return one dense vector for each input text."""


@dataclass(frozen=True)
class HashingEmbeddingProvider:
    """Offline embedding provider used when no neural model is installed.

    It is deterministic, dependency-free, and good enough for validating the
    vector-search pipeline. Production runs can replace it with a Chinese
    sentence embedding model such as bge-m3 or bge-large-zh.
    """

    dimension: int = 384
    name: str = "hashing-ngram-384"

    def encode(self, texts: list[str]) -> list[list[float]]:
        return [self._encode_one(text) for text in texts]

    def _encode_one(self, text: str) -> list[float]:
        vector = [0.0] * self.dimension
        tokens = tokenize(text)
        if not tokens:
            return vector

        for token in tokens:
            digest = hashlib.blake2b(token.encode("utf-8"), digest_size=8).digest()
            bucket = int.from_bytes(digest[:4], "little") % self.dimension
            sign = 1.0 if digest[4] % 2 == 0 else -1.0
            weight = 1.0 + min(len(token), 4) * 0.1
            vector[bucket] += sign * weight

        return normalize_vector(vector)


class SentenceTransformerEmbeddingProvider:
    """Optional adapter for local sentence-transformers models.

    Set TCM_EMBEDDING_MODEL to a local model directory or an installed model
    name. The project does not download models automatically.
    """

    def __init__(self, model_name_or_path: str | None = None) -> None:
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError as exc:
            raise RuntimeError(
                "sentence-transformers is not installed; use HashingEmbeddingProvider "
                "or install it with a local Chinese embedding model."
            ) from exc

        self.model_name_or_path = model_name_or_path or os.getenv("TCM_EMBEDDING_MODEL")
        if not self.model_name_or_path:
            raise RuntimeError("TCM_EMBEDDING_MODEL is not set.")
        self.model = SentenceTransformer(self.model_name_or_path)
        self.name = f"sentence-transformers:{self.model_name_or_path}"

    def encode(self, texts: list[str]) -> list[list[float]]:
        vectors = self.model.encode(texts, normalize_embeddings=True)
        return [list(map(float, vector)) for vector in vectors]


def normalize_vector(vector: list[float]) -> list[float]:
    norm = math.sqrt(sum(value * value for value in vector))
    if norm == 0:
        return vector
    return [value / norm for value in vector]


def dense_cosine(left: list[float], right: list[float]) -> float:
    if not left or not right or len(left) != len(right):
        return 0.0
    return sum(a * b for a, b in zip(left, right))


@dataclass
class VectorSearchIndex:
    records: list[Record]
    provider: EmbeddingProvider
    vectors: list[list[float]]

    @classmethod
    def build(
        cls,
        records: list[Record],
        provider: EmbeddingProvider | None = None,
    ) -> "VectorSearchIndex":
        provider = provider or HashingEmbeddingProvider()
        vectors = provider.encode([record.retrieval_text for record in records])
        return cls(records=records, provider=provider, vectors=vectors)

    def search(self, query: str, top_k: int = 3) -> list[tuple[Record, float]]:
        query_vector = self.provider.encode([query])[0]
        scored: list[tuple[Record, float]] = []

        for record, vector in zip(self.records, self.vectors):
            vector_score = dense_cosine(query_vector, vector)
            lexical_score = keyword_score(query, record)
            score = vector_score * 0.75 + lexical_score * 0.25
            scored.append((record, score))

        scored.sort(key=lambda item: item[1], reverse=True)
        return scored[:top_k]


def retrieve_by_embedding(
    records: list[Record],
    query: str,
    top_k: int = 3,
    provider: EmbeddingProvider | None = None,
) -> list[tuple[Record, float]]:
    index = VectorSearchIndex.build(records, provider=provider)
    return index.search(query, top_k=top_k)
