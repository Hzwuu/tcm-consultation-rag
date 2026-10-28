from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from tcm_agent import load_records, retrieve_with_details
from tcm_agent.config import DEFAULT_SOURCED_KB_PATH

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


CASES = [
    {"id": "S001", "query": "腰膝冷痛，畏寒肢冷，夜尿多", "expected_names": ["肾阳虚证"]},
    {"id": "S002", "query": "心悸，胸闷，活动后气短，容易出汗", "expected_names": ["心气虚证"]},
    {"id": "S003", "query": "干咳少痰，声音嘶哑，潮热盗汗", "expected_names": ["肺阴虚证"]},
]


def main() -> int:
    errors: list[str] = []
    records = load_records(DEFAULT_SOURCED_KB_PATH)

    print("========== 来源可追溯知识库检索评估 ==========")
    print(f"知识库：{DEFAULT_SOURCED_KB_PATH}")
    print(f"记录数：{len(records)}")
    print("")

    for case in CASES:
        matches, analysis = retrieve_with_details(records, case["query"], top_k=3)
        if not matches:
            errors.append(f"{case['id']} 没有召回结果")
            continue
        record, score, hits = matches[0]
        name_ok = record.name in case["expected_names"]
        source_ok = bool(record.source_title and record.source_url)
        review_ok = bool(record.review_status)
        if not name_ok:
            errors.append(f"{case['id']} Top1={record.name}，期望 {case['expected_names']}")
        if not source_ok:
            errors.append(f"{case['id']} Top1 缺少来源字段")
        if not review_ok:
            errors.append(f"{case['id']} Top1 缺少审核状态")
        print(
            f"{case['id']} | {case['query']} -> {record.name}（相关度 {score:.3f}）"
            f" | 症状 {hits} | 来源 {record.source_title or '缺'} | 审核 {record.review_status or '缺'}"
        )
        print(f"     来源定位：{record.source_locator or '缺'}")

    if errors:
        print("")
        print("发现问题：")
        for error in errors:
            print("- " + error)
        return 1

    print("")
    print("评估通过：来源版知识库可召回，并带来源与审核状态。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
