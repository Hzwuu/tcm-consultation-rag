from __future__ import annotations

import json
import math
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from tcm_agent.config import DEFAULT_DETAILS_KB_PATH, DEFAULT_VECTOR_INDEX_PATH
from tcm_agent.knowledge_base import load_records

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def main() -> int:
    errors: list[str] = []
    records = load_records(DEFAULT_DETAILS_KB_PATH)

    if not DEFAULT_VECTOR_INDEX_PATH.exists():
        errors.append(f"missing vector index: {DEFAULT_VECTOR_INDEX_PATH}")
        payload = {}
    else:
        payload = json.loads(DEFAULT_VECTOR_INDEX_PATH.read_text(encoding="utf-8"))

    items = payload.get("items", []) if isinstance(payload, dict) else []
    if payload.get("record_count") != len(records):
        errors.append(
            f"record_count mismatch: {payload.get('record_count')} != {len(records)}"
        )
    if len(items) != len(records):
        errors.append(f"item count mismatch: {len(items)} != {len(records)}")
    if not payload.get("provider"):
        errors.append("missing provider")

    seen_ids: set[str] = set()
    for item in items:
        item_id = item.get("id", "")
        vector = item.get("vector", [])
        if not item_id:
            errors.append("item missing id")
        if item_id in seen_ids:
            errors.append(f"duplicate vector id: {item_id}")
        seen_ids.add(item_id)
        if not isinstance(vector, list) or len(vector) != 384:
            errors.append(f"{item_id} vector dimension must be 384")
            continue
        norm = math.sqrt(sum(float(value) * float(value) for value in vector))
        if not 0.99 <= norm <= 1.01:
            errors.append(f"{item_id} vector norm out of range: {norm:.4f}")

    print("========== 本地向量索引校验 ==========")
    print(f"文件：{DEFAULT_VECTOR_INDEX_PATH}")
    print(f"知识库记录数：{len(records)}")
    print(f"向量条目数：{len(items)}")
    print(f"Embedding provider：{payload.get('provider', '<missing>')}")

    if errors:
        print("")
        print("发现问题：")
        for error in errors:
            print("- " + error)
        return 1

    print("校验通过：向量索引记录数、唯一 ID、维度和归一化均满足当前要求。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
