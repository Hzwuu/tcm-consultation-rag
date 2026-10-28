"""TCM consultation assistant core package."""

from .consultation import ConsultationState, TCMConsultAgent
from .embedding_retrieval import HashingEmbeddingProvider, VectorSearchIndex, retrieve_by_embedding
from .generation import GroundedRAGGenerator, LLMRenderResult
from .knowledge_base import load_records
from .llm_generation import DeepSeekGenerator, LLMResult
from .llm_providers import PROVIDER_PRESETS, list_provider_models, make_generator
from .llm_slots import extract_slots_with_llm
from .query_understanding import QueryAnalysis, analyze_query, canonical_variants, detect_terms
from .retrieval import retrieve, retrieve_with_details
from .safety import detect_red_flags
from .structured_slots import extract_slots, format_slots, merge_slots

__all__ = [
    "ConsultationState",
    "DeepSeekGenerator",
    "HashingEmbeddingProvider",
    "GroundedRAGGenerator",
    "LLMResult",
    "LLMRenderResult",
    "PROVIDER_PRESETS",
    "QueryAnalysis",
    "TCMConsultAgent",
    "VectorSearchIndex",
    "analyze_query",
    "canonical_variants",
    "detect_red_flags",
    "detect_terms",
    "extract_slots",
    "extract_slots_with_llm",
    "format_slots",
    "load_records",
    "list_provider_models",
    "make_generator",
    "merge_slots",
    "retrieve",
    "retrieve_by_embedding",
    "retrieve_with_details",
]
