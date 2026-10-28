from __future__ import annotations

import csv
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from tcm_agent import detect_red_flags, load_records
from tcm_agent.config import DEFAULT_EVAL_CASES_PATH, DEFAULT_KB_PATH
from tcm_agent.embedding_retrieval import VectorSearchIndex

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def load_cases(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as file:
        return list(csv.DictReader(file))


def parse_bool(value: str) -> bool:
    return value.strip().lower() in {"true", "1", "yes", "y"}


def evaluate(kb_path: Path = DEFAULT_KB_PATH, cases_path: Path = DEFAULT_EVAL_CASES_PATH) -> int:
    records = load_records(kb_path)
    cases = load_cases(cases_path)
    index = VectorSearchIndex.build(records)

    top3_pass = 0
    red_flag_pass = 0

    print("========== Embedding 向量检索基础评估 ==========")
    print(f"Embedding provider：{index.provider.name}")
    print(f"用例数：{len(cases)}")

    rows: list[str] = []
    for case in cases:
        matches = index.search(case["query"], top_k=3)
        top_names = [record.name for record, _score in matches]
        expected_top1 = case["expected_top1"]
        actual_red_flag = bool(detect_red_flags(case["query"]))
        expected_red_flag = parse_bool(case["should_red_flag"])

        top3_ok = True if not expected_top1 else expected_top1 in top_names
        red_flag_ok = actual_red_flag == expected_red_flag
        top3_pass += int(top3_ok)
        red_flag_pass += int(red_flag_ok)

        rows.append(
            f"{case['id']} | Top3 {top_names} / {expected_top1 or '不要求'} "
            f"({top3_ok}) | 红旗 {actual_red_flag} / {expected_red_flag} ({red_flag_ok})"
        )

    print(f"Top3 命中：{top3_pass}/{len(cases)}")
    print(f"红旗识别：{red_flag_pass}/{len(cases)}")
    print("")
    print("\n".join(rows))
    return 0 if top3_pass == len(cases) and red_flag_pass == len(cases) else 1


if __name__ == "__main__":
    raise SystemExit(evaluate())
