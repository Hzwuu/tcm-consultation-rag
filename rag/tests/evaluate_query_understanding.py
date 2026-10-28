from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from tcm_agent import analyze_query, load_records, retrieve_with_details
from tcm_agent.config import DEFAULT_KB_PATH

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


TYPO_CASES = [
    {
        "id": "Q001",
        "text": "嗓子咽通，发烧怕冷",
        "expected_terms": ["咽痛", "发热", "怕冷"],
        "expected_correction": "咽通→咽痛",
    },
    {
        "id": "Q002",
        "text": "腰膝酸软，夜里盗汗，手脚心发热",
        "expected_terms": ["腰膝酸软", "盗汗", "潮热"],
    },
    {
        "id": "Q003",
        "text": "胃胀，打嗝有酸腐味，不想吃饭",
        "expected_terms": ["胃胀", "反酸", "食欲不振"],
    },
]

RETRIEVAL_CASES = [
    {"id": "R001", "query": "嗓子咽通，发烧怕冷", "expected_top1": "风热感冒", "min_hits": 2},
    {"id": "R002", "query": "胃胀 打嗝有酸腐味 不想吃饭", "expected_top1": "食积停滞", "min_hits": 2},
    {"id": "R003", "query": "怕冷 发热轻 流清鼻涕 不渴", "expected_top1": "风寒感冒", "min_hits": 3},
]


def main() -> int:
    errors: list[str] = []

    print("========== 症状理解与多症状检索评估 ==========")
    print("")
    print("--- 同义词 / 错别字 / 多症状识别 ---")
    for case in TYPO_CASES:
        analysis = analyze_query(case["text"])
        missing = [term for term in case["expected_terms"] if term not in analysis.terms]
        if missing:
            errors.append(f"{case['id']} 缺少症状：{missing}")
        expected_correction = case.get("expected_correction")
        if expected_correction and expected_correction not in analysis.corrections:
            errors.append(
                f"{case['id']} 缺少纠正：{expected_correction}（实际 {analysis.corrections}）"
            )
        print(
            f"{case['id']} | {case['text']} -> 症状 {analysis.terms} | 纠正 {analysis.corrections}"
        )

    print("")
    print("--- 多症状检索（基础 15 条知识库） ---")
    records = load_records(DEFAULT_KB_PATH)
    for case in RETRIEVAL_CASES:
        matches, _analysis = retrieve_with_details(records, case["query"], top_k=3)
        top1 = matches[0][0].name if matches else ""
        hits = matches[0][2] if matches else []
        top1_ok = top1 == case["expected_top1"]
        hits_ok = len(hits) >= case["min_hits"]
        if not top1_ok:
            errors.append(f"{case['id']} Top1={top1}，期望 {case['expected_top1']}")
        if not hits_ok:
            errors.append(f"{case['id']} 命中症状过少：{hits}")
        print(
            f"{case['id']} | {case['query']} -> Top1 {top1} ({top1_ok}) | 命中症状 {hits} ({hits_ok})"
        )

    if errors:
        print("")
        print("发现问题：")
        for error in errors:
            print("- " + error)
        return 1

    print("")
    print("评估通过：同义词、轻微错别字和多症状叠加均已生效。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
