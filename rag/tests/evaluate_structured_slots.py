from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from tcm_agent import extract_slots

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


CASES = [
    {
        "id": "S001",
        "text": "最近三天发热怕冷，无汗，口渴想喝冷水，大便干结，睡不着。",
        "expected": {
            "寒热": ["发热", "怕冷"],
            "出汗": ["无汗"],
            "口渴": ["口渴", "喜冷饮"],
            "大便": ["便秘"],
            "睡眠": ["失眠"],
            "持续时间": ["三天"],
        },
    },
    {
        "id": "S002",
        "text": "夜里盗汗，多梦，五心烦热，腰膝酸软，最近压力大。",
        "expected": {
            "寒热": ["潮热"],
            "出汗": ["盗汗"],
            "睡眠": ["多梦"],
            "情绪": ["焦虑紧张"],
            "疼痛部位": ["腰膝酸软"],
            "持续时间": ["最近"],
        },
    },
    {
        "id": "S003",
        "text": "昨天吃多后胃胀，大便酸臭，有点恶心，没有剧烈腹痛。",
        "expected": {
            "大便": ["酸臭"],
            "持续时间": ["昨天"],
            "严重程度": ["轻微"],
        },
        "unexpected": {
            "疼痛部位": ["腹痛"],
            "严重程度": ["剧烈"],
        },
    },
    {
        "id": "S004",
        "text": "小便黄，夜尿多，长期睡不着，急躁易怒。",
        "expected": {
            "小便": ["尿黄", "尿频"],
            "睡眠": ["失眠"],
            "情绪": ["烦躁易怒"],
            "持续时间": ["长期"],
        },
    },
]


def main() -> int:
    errors: list[str] = []

    print("========== 结构化问诊槽位抽取评估 ==========")
    print(f"用例数：{len(CASES)}")

    for case in CASES:
        slots = extract_slots(case["text"])
        expected = case.get("expected", {})
        unexpected = case.get("unexpected", {})

        for slot, values in expected.items():
            for value in values:
                if value not in slots.get(slot, []):
                    errors.append(f"{case['id']} missing {slot}={value}")

        for slot, values in unexpected.items():
            for value in values:
                if value in slots.get(slot, []):
                    errors.append(f"{case['id']} unexpected {slot}={value}")

        print(f"{case['id']} | {slots}")

    if errors:
        print("")
        print("发现问题：")
        for error in errors:
            print("- " + error)
        return 1

    print("槽位抽取评估通过：核心槽位、持续时间和否定表达均满足当前要求。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
