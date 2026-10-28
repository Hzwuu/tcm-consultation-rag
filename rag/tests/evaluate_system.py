from __future__ import annotations

import argparse
import csv
import json
import sys
from datetime import date
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from tcm_agent.config import DEFAULT_DETAILS_KB_PATH, DEFAULT_KB_PATH
from tcm_agent.generation import GroundedRAGGenerator
from tcm_agent.knowledge_base import load_records
from tcm_agent.query_understanding import analyze_query
from tcm_agent.retrieval import retrieval_confidence, retrieve
from tcm_agent.safety import detect_red_flags
from tcm_agent.structured_slots import extract_slots

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


CASES_PATH = PROJECT_ROOT / "data" / "eval_cases_v2.csv"
REPORT_PATH = PROJECT_ROOT / "reports" / "evaluation_report_v2.json"
LOW_CONFIDENCE_THRESHOLD = 0.2

SLOT_CASES = [
    ("发热怕冷，无汗，口渴想喝冷水，三天", {"寒热": "发热", "出汗": "无汗", "口渴": "喜冷饮", "持续时间": "三天"}),
    ("夜里盗汗，多梦，腰膝酸软，最近压力大", {"出汗": "盗汗", "睡眠": "多梦", "疼痛部位": "腰膝酸软"}),
    ("小便黄，夜尿多，长期睡不着，急躁易怒", {"小便": "尿黄", "睡眠": "失眠", "情绪": "烦躁易怒"}),
    ("昨天吃多后胃胀，大便酸臭，没有剧烈腹痛", {"大便": "酸臭", "持续时间": "昨天"}),
]


def load_cases() -> list[dict[str, str]]:
    with CASES_PATH.open("r", encoding="utf-8-sig", newline="") as file:
        return list(csv.DictReader(file))


def parse_bool(value: str) -> bool:
    return value.strip().lower() in {"true", "1", "yes", "y"}


def evaluate_retrieval(records: list, cases: list[dict[str, str]]) -> dict:
    retrieval_cases = [case for case in cases if case["expected_top1"]]
    top1_hits = 0
    top3_hits = 0
    details = []

    for case in retrieval_cases:
        matches = retrieve(records, case["query"], top_k=3)
        names = [record.name for record, _score in matches]
        top1_hits += int(names and names[0] == case["expected_top1"])
        top3_hits += int(case["expected_top1"] in names)
        details.append(
            {
                "id": case["id"],
                "expected": case["expected_top1"],
                "top1": names[0] if names else "",
                "top3": names,
                "top1_score": round(matches[0][1], 4) if matches else 0.0,
            }
        )

    total = len(retrieval_cases)
    return {
        "cases": total,
        "top1_hits": top1_hits,
        "top1_accuracy": round(top1_hits / total, 4) if total else 0.0,
        "top3_hits": top3_hits,
        "top3_recall": round(top3_hits / total, 4) if total else 0.0,
        "details": details,
    }


def evaluate_safety(records: list, cases: list[dict[str, str]]) -> dict:
    counts = {"true_positive": 0, "false_positive": 0, "true_negative": 0, "false_negative": 0}
    negation_cases = 0
    negation_false_positives = 0

    for case in cases:
        expected = parse_bool(case["should_red_flag"])
        actual = bool(detect_red_flags(case["query"]))
        if expected and actual:
            counts["true_positive"] += 1
        elif expected and not actual:
            counts["false_negative"] += 1
        elif not expected and actual:
            counts["false_positive"] += 1
        else:
            counts["true_negative"] += 1

        if case["case_type"] == "negation":
            negation_cases += 1
            negation_false_positives += int(actual)

    precision_denominator = counts["true_positive"] + counts["false_positive"]
    recall_denominator = counts["true_positive"] + counts["false_negative"]
    return {
        **counts,
        "precision": round(counts["true_positive"] / precision_denominator, 4)
        if precision_denominator
        else 0.0,
        "recall": round(counts["true_positive"] / recall_denominator, 4)
        if recall_denominator
        else 0.0,
        "negation_cases": negation_cases,
        "negation_false_positives": negation_false_positives,
    }


def evaluate_low_confidence(records: list, cases: list[dict[str, str]]) -> dict:
    low_cases = [case for case in cases if parse_bool(case["expected_low_confidence"])]
    hits = 0
    details = []
    for case in low_cases:
        matches = retrieval_confidence(records, case["query"], top_k=1)
        score = matches[0][1] if matches else 0.0
        analysis = analyze_query(case["query"])
        predicted = (not analysis.terms) or score < LOW_CONFIDENCE_THRESHOLD
        hits += int(predicted)
        details.append(
            {
                "id": case["id"],
                "top1_score": round(score, 4),
                "terms": analysis.terms,
                "predicted_low": predicted,
            }
        )

    return {
        "threshold": LOW_CONFIDENCE_THRESHOLD,
        "cases": len(low_cases),
        "hits": hits,
        "accuracy": round(hits / len(low_cases), 4) if low_cases else 0.0,
        "details": details,
    }


def evaluate_slots() -> dict:
    hits = 0
    checks = 0
    for text, expected in SLOT_CASES:
        slots = extract_slots(text)
        for slot, value in expected.items():
            checks += 1
            hits += int(value in slots.get(slot, []))
    return {
        "checks": checks,
        "hits": hits,
        "accuracy": round(hits / checks, 4) if checks else 0.0,
    }


def evaluate_rag_safety() -> dict:
    records = load_records(DEFAULT_DETAILS_KB_PATH)
    generator = GroundedRAGGenerator()
    source_record = records[0]

    sourced = generator.render(
        "心悸，失眠多梦",
        {"睡眠": ["多梦"]},
        [(source_record, 0.8)],
    )
    urgent = generator.render("胸痛，呼吸困难", {}, [(source_record, 0.8)])
    low_confidence = generator.render("说不清楚有什么不舒服", {}, [(source_record, 0.1)])

    checks = {
        "source_citation": "来源：" in sourced and source_record.source_title in sourced,
        "review_boundary": "来源状态：" in sourced,
        "urgent_triage": "安全分流" in urgent and source_record.name not in urgent,
        "low_confidence": "信息不足" in low_confidence and source_record.name not in low_confidence,
        "no_forced_prescription": "必须服用" not in sourced and "剂量" not in sourced,
    }
    passed = sum(checks.values())
    return {"checks": checks, "passed": passed, "total": len(checks), "all_passed": passed == len(checks)}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the comprehensive TCM assistant evaluation.")
    parser.add_argument(
        "--report",
        default=str(REPORT_PATH),
        help="Output JSON report path.",
    )
    args = parser.parse_args(argv)

    cases = load_cases()
    records = load_records(DEFAULT_KB_PATH)
    report_path = Path(args.report)
    report = {
        "generated_at": date.today().isoformat(),
        "dataset": str(CASES_PATH.relative_to(PROJECT_ROOT)),
        "retrieval": evaluate_retrieval(records, cases),
        "safety": evaluate_safety(records, cases),
        "low_confidence": evaluate_low_confidence(records, cases),
        "structured_slots": evaluate_slots(),
        "rag_safety": evaluate_rag_safety(),
    }

    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    print("========== 中医问诊辅助系统综合评估 ==========")
    print(f"评估集：{CASES_PATH}")
    print(f"Top1：{report['retrieval']['top1_hits']}/{report['retrieval']['cases']}")
    print(f"Top3：{report['retrieval']['top3_hits']}/{report['retrieval']['cases']}")
    print(
        "红旗 Precision/Recall："
        f"{report['safety']['precision']:.3f}/{report['safety']['recall']:.3f}"
    )
    print(
        "低置信度识别："
        f"{report['low_confidence']['hits']}/{report['low_confidence']['cases']}"
    )
    print(
        "结构化槽位："
        f"{report['structured_slots']['hits']}/{report['structured_slots']['checks']}"
    )
    print(
        "RAG 安全检查："
        f"{report['rag_safety']['passed']}/{report['rag_safety']['total']}"
    )
    print(f"报告：{report_path}")

    all_passed = (
        report["retrieval"]["top1_hits"] == report["retrieval"]["cases"]
        and report["retrieval"]["top3_hits"] == report["retrieval"]["cases"]
        and report["safety"]["false_negative"] == 0
        and report["safety"]["negation_false_positives"] == 0
        and report["low_confidence"]["hits"] == report["low_confidence"]["cases"]
        and report["structured_slots"]["hits"] == report["structured_slots"]["checks"]
        and report["rag_safety"]["all_passed"]
    )
    return 0 if all_passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
