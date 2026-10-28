from __future__ import annotations

import math
import re
from collections import Counter, defaultdict
from typing import Iterable

from .models import Record
from .query_understanding import QueryAnalysis, analyze_query, canonical_variants
from .safety import normalize


def tokenize(text: str) -> list[str]:
    text = normalize(text)
    tokens: list[str] = []

    cjk_chars = re.findall(r"[\u4e00-\u9fff]", text)
    joined = "".join(cjk_chars)
    tokens.extend(cjk_chars)
    tokens.extend(joined[i : i + 2] for i in range(max(0, len(cjk_chars) - 1)))
    tokens.extend(joined[i : i + 3] for i in range(max(0, len(cjk_chars) - 2)))
    tokens.extend(re.findall(r"[a-z0-9]+", text))
    return [token for token in tokens if token]


def build_idf(records: list[Record]) -> dict[str, float]:
    document_count = len(records)
    document_frequency: dict[str, int] = defaultdict(int)

    for record in records:
        for token in set(tokenize(record.retrieval_text)):
            document_frequency[token] += 1

    return {
        token: math.log((document_count + 1) / (frequency + 1)) + 1
        for token, frequency in document_frequency.items()
    }


def vectorize(tokens: Iterable[str], idf: dict[str, float]) -> dict[str, float]:
    counts = Counter(tokens)
    if not counts:
        return {}

    total = sum(counts.values())
    return {
        token: (count / total) * idf.get(token, 1.0)
        for token, count in counts.items()
    }


def cosine(left: dict[str, float], right: dict[str, float]) -> float:
    if not left or not right:
        return 0.0

    shared = set(left) & set(right)
    dot = sum(left[token] * right[token] for token in shared)
    left_norm = math.sqrt(sum(value * value for value in left.values()))
    right_norm = math.sqrt(sum(value * value for value in right.values()))
    if left_norm == 0 or right_norm == 0:
        return 0.0
    return dot / (left_norm * right_norm)


def keyword_score(query: str, record: Record) -> float:
    query_tokens = set(tokenize(query))
    record_tokens = set(tokenize(record.retrieval_text))
    if not query_tokens:
        return 0.0

    overlap = len(query_tokens & record_tokens) / len(query_tokens)
    direct_bonus = 0.0
    normalized_query = normalize(query)
    for word in re.split(r"[；;，,、\s]+", record.retrieval_keywords):
        word = normalize(word)
        if word and word in normalized_query:
            direct_bonus += 0.08

    return min(1.0, overlap + direct_bonus)


def symptom_coverage(record: Record, terms: list[str]) -> tuple[float, list[str]]:
    """Score how many distinct symptoms in the query are covered by a record."""
    if not terms:
        return 0.0, []

    target = normalize(
        "；".join(
            [
                record.name,
                record.category,
                record.core_symptoms,
                record.differentiation_points,
                record.common_triggers,
                record.retrieval_keywords,
            ]
        )
    )
    core = normalize(record.core_symptoms)
    hits: list[str] = []
    core_hits = 0

    for term in terms:
        variants = canonical_variants(term)
        if any(normalize(variant) in target for variant in variants):
            hits.append(term)
            if any(normalize(variant) in core for variant in variants):
                core_hits += 1

    if not hits:
        return 0.0, []

    coverage = len(hits) / len(terms)
    bonus = min(0.2, 0.05 * core_hits)
    return min(1.0, coverage + bonus), hits


def retrieve_with_details(
    records: list[Record],
    query: str,
    top_k: int = 3,
) -> tuple[list[tuple[Record, float, list[str]]], QueryAnalysis]:
    """Retrieve candidates and keep the symptom analysis for display and tests."""
    analysis = analyze_query(query)
    expanded_query = query
    if analysis.terms:
        expanded_query = "；".join([query, analysis.corrected, "；".join(analysis.terms)])

    idf = build_idf(records)
    record_vectors = {
        record.id: vectorize(tokenize(record.retrieval_text), idf)
        for record in records
    }
    query_vector = vectorize(tokenize(expanded_query), idf)

    scored: list[tuple[Record, float, list[str]]] = []
    for record in records:
        semantic = cosine(query_vector, record_vectors[record.id])
        lexical = keyword_score(expanded_query, record)
        base = semantic * 0.65 + lexical * 0.35
        coverage, hits = symptom_coverage(record, analysis.terms)
        score = base * 0.8 + coverage * 0.2 if analysis.terms else base
        scored.append((record, score, hits))

    scored.sort(key=lambda item: item[1], reverse=True)
    return scored[:top_k], analysis


def retrieve(records: list[Record], query: str, top_k: int = 3) -> list[tuple[Record, float]]:
    scored, _analysis = retrieve_with_details(records, query, top_k=top_k)
    return [(record, score) for record, score, _hits in scored]


def retrieval_confidence(records: list[Record], query: str, top_k: int = 1) -> list[tuple[Record, float]]:
    """Return base semantic/lexical scores without the multi-symptom bonus.

    Low-confidence decisions must not be inflated merely because a vague query
    happens to contain one recognizable symptom word.
    """
    analysis = analyze_query(query)
    expanded_query = query
    if analysis.terms:
        expanded_query = "；".join([query, analysis.corrected, "；".join(analysis.terms)])

    idf = build_idf(records)
    record_vectors = {
        record.id: vectorize(tokenize(record.retrieval_text), idf)
        for record in records
    }
    query_vector = vectorize(tokenize(expanded_query), idf)

    scored: list[tuple[Record, float]] = []
    for record in records:
        semantic = cosine(query_vector, record_vectors[record.id])
        lexical = keyword_score(expanded_query, record)
        scored.append((record, semantic * 0.65 + lexical * 0.35))

    scored.sort(key=lambda item: item[1], reverse=True)
    return scored[:top_k]
