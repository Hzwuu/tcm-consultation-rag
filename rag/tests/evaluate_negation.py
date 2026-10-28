from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from tcm_agent import load_records
from tcm_agent.config import DEFAULT_KB_PATH
from tcm_agent.query_understanding import analyze_query
from tcm_agent.retrieval import retrieve
from tcm_agent.safety import detect_red_flags, is_negated
from tcm_agent.structured_slots import extract_slots

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def main() -> int:
    errors: list[str] = []

    red_flag_cases = [
        ("胸痛，呼吸困难", ["胸痛", "呼吸困难"]),
        ("没有胸痛", []),
        ("没有剧烈腹痛", []),
        ("没有胸痛，但现在胸痛", ["胸痛"]),
        ("昨天没有黑便，今天黑便", ["黑便"]),
        ("无胸痛，伴呼吸困难", ["呼吸困难"]),
        ("没有呕血，但是黑便", ["黑便"]),
    ]
    print("========== 否定识别回归 ==========")
    for text, expected in red_flag_cases:
        actual = detect_red_flags(text)
        ok = sorted(actual) == sorted(expected)
        if not ok:
            errors.append(f"红旗：{text!r} 期望 {expected} 实际 {actual}")
        print(f"红旗 | {text!r} -> {actual} {'OK' if ok else 'FAIL'}")

    term_cases = [
        ("没有咳嗽，没有发热，只是有点胃胀", {"胃胀"}, {"咳嗽", "发热"}),
        ("不发热", set(), {"发热"}),
        ("不渴", {"不渴"}, set()),
        ("有点不舒服胃胀", {"胃胀"}, set()),
        ("发热，没有咳嗽", {"发热"}, {"咳嗽"}),
    ]
    for text, expected, forbidden in term_cases:
        terms = set(analyze_query(text).terms)
        ok = expected <= terms and not (forbidden & terms)
        if not ok:
            errors.append(f"术语：{text!r} 期望含 {expected}、不含 {forbidden}，实际 {terms}")
        print(f"术语 | {text!r} -> {sorted(terms)} {'OK' if ok else 'FAIL'}")

    records = load_records(DEFAULT_KB_PATH)
    query = "没有咳嗽，没有发热，只是有点胃胀"
    hits = retrieve(records, query, top_k=3)
    top_names = [record.name for record, _score in hits]
    if top_names and top_names[0] == "痰湿咳嗽":
        errors.append(f"检索：否认的症状把候选带偏：{top_names}")
    print(f"检索 | {query!r} -> Top3 {top_names}")

    slot_cases = [
        ("没有发热", {}),
        ("发热，没有咳嗽", {"寒热": ["发热"]}),
        ("没有发热，但后来发热了", {"寒热": ["发热"]}),
        ("无汗", {"出汗": ["无汗"]}),
    ]
    for text, expected in slot_cases:
        slots = extract_slots(text)
        ok = slots == expected
        if not ok:
            errors.append(f"槽位：{text!r} 期望 {expected} 实际 {slots}")
        print(f"槽位 | {text!r} -> {slots} {'OK' if ok else 'FAIL'}")

    if not is_negated("没有胸痛", "胸痛"):
        errors.append("is_negated('没有胸痛', '胸痛') 应为 True")
    if is_negated("没有胸痛，但现在胸痛", "胸痛"):
        errors.append("is_negated 混合句（先否后肯）应为 False")

    print()
    if errors:
        print("发现问题：")
        for error in errors:
            print("- " + error)
        return 1
    print("否定识别评估通过：跨句不再误吞、后置肯定不再被掩盖、否认症状不参与检索。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
