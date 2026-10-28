from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from tcm_agent.config import DEFAULT_DETAILS_KB_PATH, DEFAULT_VECTOR_INDEX_PATH
from tcm_agent.embedding_retrieval import VectorSearchIndex
from tcm_agent.knowledge_base import load_records


def build_vector_index(kb_path: Path, output_path: Path) -> None:
    records = load_records(kb_path)
    index = VectorSearchIndex.build(records)

    payload = {
        "schema_version": "1.0",
        "created_at": date.today().isoformat(),
        "source_kb": str(kb_path.relative_to(PROJECT_ROOT)),
        "record_count": len(records),
        "provider": index.provider.name,
        "items": [
            {
                "id": record.id,
                "name": record.name,
                "category": record.category,
                "source_title": record.source_title,
                "review_status": record.review_status,
                "text": record.retrieval_text,
                "vector": vector,
            }
            for record, vector in zip(index.records, index.vectors)
        ],
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"wrote {len(records)} vectors to {output_path}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build local vector index JSON.")
    parser.add_argument("--kb", default=str(DEFAULT_DETAILS_KB_PATH), help="Knowledge base CSV path")
    parser.add_argument("--out", default=str(DEFAULT_VECTOR_INDEX_PATH), help="Vector index JSON path")
    args = parser.parse_args(argv)

    build_vector_index(Path(args.kb), Path(args.out))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
