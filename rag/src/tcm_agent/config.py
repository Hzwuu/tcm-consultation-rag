from __future__ import annotations

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"
DEFAULT_KB_PATH = DATA_DIR / "tcm_knowledge_base_v1.csv"
DEFAULT_DETAILS_KB_PATH = DATA_DIR / "tcm_syndrome_details_v2_source_backed.csv"
DEFAULT_SOURCED_KB_PATH = DEFAULT_DETAILS_KB_PATH
DEFAULT_EVAL_CASES_PATH = DATA_DIR / "eval_cases.csv"
DEFAULT_VECTOR_INDEX_PATH = DATA_DIR / "vector_index_hashing_v1.json"
