from __future__ import annotations

import csv
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DETAILS_PATH = PROJECT_ROOT / "data" / "tcm_syndrome_details_v2_source_backed.csv"

REQUIRED_FIELDS = [
    "id",
    "name",
    "core_symptoms",
    "tongue_pulse",
    "differentiation_points",
    "follow_up_questions",
    "source_title",
    "source_url",
    "source_locator",
    "evidence_note",
]


def main() -> int:
    with DETAILS_PATH.open("r", encoding="utf-8-sig", newline="") as file:
        rows = list(csv.DictReader(file))

    errors: list[str] = []
    if len(rows) < 10:
        errors.append(f"expected at least 10 source-backed detail rows, got {len(rows)}")

    ids = [row["id"] for row in rows]
    if len(ids) != len(set(ids)):
        errors.append("duplicate ids found")

    for row in rows:
        for field in REQUIRED_FIELDS:
            if not row.get(field, "").strip():
                errors.append(f"{row.get('id', '<missing id>')} missing {field}")
        review_status = row.get("review_status", "").strip()
        if not any(marker in review_status for marker in ["待专业审核", "待中医专业审核", "安全优先"]):
            errors.append(f"{row.get('id', '<missing id>')} review_status must expose review boundary")

    print("========== 临床详情知识库校验 ==========")
    print(f"文件：{DETAILS_PATH}")
    print(f"记录数：{len(rows)}")
    print(f"必填字段：{', '.join(REQUIRED_FIELDS)}")

    if errors:
        print("")
        print("发现问题：")
        for error in errors:
            print("- " + error)
        return 1

    print("校验通过：临床详情条目均包含来源、症状、舌脉/追问和审核边界。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
