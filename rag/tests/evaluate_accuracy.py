from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import defaultdict
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from tcm_agent import analyze_query, detect_red_flags, load_records, retrieve_with_details
from tcm_agent.config import DEFAULT_KB_PATH
from tcm_agent.retrieval import retrieval_confidence

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


CASES_PATH = PROJECT_ROOT / "data" / "accuracy_cases_v1.csv"
REPORT_PATH = PROJECT_ROOT / "reports" / "accuracy_report_v1.json"
LOW_CONFIDENCE_THRESHOLD = 0.2

CAVEAT = (
    "自建测试集：用例由知识库症状改写、口语化改写和人工场景编写，"
    "只代表本测试集上的表现，不等于临床准确率，也不代表真实用户分布。"
)


def parse_bool(value: str) -> bool:
    return str(value).strip().lower() in {"true", "1", "yes", "y"}


def load_cases() -> list[dict[str, str]]:
    with CASES_PATH.open("r", encoding="utf-8-sig", newline="") as file:
        return list(csv.DictReader(file))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="自建测试集准确率评测")
    parser.add_argument("--report", default=str(REPORT_PATH), help="JSON 报告输出路径")
    args = parser.parse_args(argv)

    cases = load_cases()
    records = load_records(DEFAULT_KB_PATH)
    retrieval_cases = [case for case in cases if case["expected_top1"].strip()]

    top1_hits = 0
    top3_hits = 0
    over_refusal = 0
    details: list[dict] = []
    type_stats: dict[str, dict[str, int]] = defaultdict(lambda: {"total": 0, "top1": 0, "top3": 0})

    for case in retrieval_cases:
        matches, analysis = retrieve_with_details(records, case["query"], top_k=3)
        names = [record.name for record, _score, _hits in matches]
        top1 = names[0] if names else ""
        top3 = bool(case["expected_top1"] in names)
        top1_ok = top1 == case["expected_top1"]
        confidence_list = retrieval_confidence(records, case["query"], top_k=1)
        confidence = confidence_list[0][1] if confidence_list else 0.0
        if confidence < LOW_CONFIDENCE_THRESHOLD:
            over_refusal += 1

        top1_hits += int(top1_ok)
        top3_hits += int(top3)
        case_type = case["case_type"] or "unknown"
        type_stats[case_type]["total"] += 1
        type_stats[case_type]["top1"] += int(top1_ok)
        type_stats[case_type]["top3"] += int(top3)
        details.append(
            {
                "id": case["id"],
                "query": case["query"],
                "case_type": case_type,
                "expected": case["expected_top1"],
                "top1": top1,
                "top3": names,
                "top1_ok": top1_ok,
                "top3_ok": top3,
                "confidence": round(confidence, 4),
                "terms": analysis.terms,
                "corrections": analysis.corrections,
            }
        )

    safety_counts = {"tp": 0, "fp": 0, "tn": 0, "fn": 0}
    safety_details = []
    for case in cases:
        expected = parse_bool(case["should_red_flag"])
        actual = bool(detect_red_flags(case["query"]))
        if expected and actual:
            safety_counts["tp"] += 1
        elif expected and not actual:
            safety_counts["fn"] += 1
        elif not expected and actual:
            safety_counts["fp"] += 1
        else:
            safety_counts["tn"] += 1
        safety_details.append(
            {"id": case["id"], "query": case["query"], "expected": expected, "actual": actual}
        )

    precision_denominator = safety_counts["tp"] + safety_counts["fp"]
    recall_denominator = safety_counts["tp"] + safety_counts["fn"]
    safety = {
        **safety_counts,
        "precision": round(safety_counts["tp"] / precision_denominator, 4)
        if precision_denominator
        else 0.0,
        "recall": round(safety_counts["tp"] / recall_denominator, 4)
        if recall_denominator
        else 0.0,
        "details": safety_details,
    }

    low_cases = [case for case in cases if parse_bool(case["expected_low_confidence"])]
    low_hits = 0
    low_details = []
    for case in low_cases:
        confidence_list = retrieval_confidence(records, case["query"], top_k=1)
        confidence = confidence_list[0][1] if confidence_list else 0.0
        analysis = analyze_query(case["query"])
        predicted = (not analysis.terms) or confidence < LOW_CONFIDENCE_THRESHOLD
        low_hits += int(predicted)
        low_details.append(
            {
                "id": case["id"],
                "query": case["query"],
                "confidence": round(confidence, 4),
                "terms": analysis.terms,
                "predicted_low": predicted,
            }
        )

    retrieval_total = len(retrieval_cases)
    report = {
        "dataset": str(CASES_PATH.relative_to(PROJECT_ROOT)),
        "dataset_size": len(cases),
        "caveat": CAVEAT,
        "retrieval": {
            "cases": retrieval_total,
            "top1_hits": top1_hits,
            "top1_accuracy": round(top1_hits / retrieval_total, 4) if retrieval_total else 0.0,
            "top3_hits": top3_hits,
            "top3_recall": round(top3_hits / retrieval_total, 4) if retrieval_total else 0.0,
            "over_refusal_count": over_refusal,
            "by_type": dict(type_stats),
            "details": details,
        },
        "safety": safety,
        "low_confidence": {
            "cases": len(low_cases),
            "hits": low_hits,
            "accuracy": round(low_hits / len(low_cases), 4) if low_cases else 0.0,
            "details": low_details,
        },
    }

    report_path = Path(args.report)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    print("========== 准确率评测（自建测试集） ==========")
    print(f"评估集：{CASES_PATH}（{len(cases)} 条）")
    print(f"检索用例：{retrieval_total} 条")
    if retrieval_total:
        print(f"Top1：{top1_hits}/{retrieval_total} = {top1_hits / retrieval_total:.1%}")
        print(f"Top3：{top3_hits}/{retrieval_total} = {top3_hits / retrieval_total:.1%}")
    for case_type, stats in sorted(type_stats.items()):
        total = stats["total"]
        print(
            f"  - {case_type}: Top1 {stats['top1']}/{total}"
            f" = {stats['top1'] / total:.1%}；Top3 {stats['top3']}/{total}"
        )
    print(f"红旗 Precision/Recall：{safety['precision']:.3f}/{safety['recall']:.3f}")
    print(f"红旗误报/漏报：{safety_counts['fp']}/{safety_counts['fn']}")
    print(f"低置信度识别：{low_hits}/{len(low_cases)}")
    print(f"误拒答（有明确目标但置信度 < {LOW_CONFIDENCE_THRESHOLD}）：{over_refusal}/{retrieval_total}")
    print("")
    print(CAVEAT)
    if retrieval_total and top1_hits / retrieval_total < 0.9:
        print("注意：本次 Top1 未达到立项书中的 90% 指标；以上为真实结果，不做美化。")
    print(f"报告：{report_path}")

    return 1 if safety_counts["fn"] > 0 else 0


if __name__ == "__main__":
    raise SystemExit(main())
