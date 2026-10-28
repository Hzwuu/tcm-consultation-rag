from __future__ import annotations

import csv
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

PROJECT_ROOT = Path(__file__).resolve().parents[1]
KB_PATH = PROJECT_ROOT / "data" / "tcm_syndrome_index_v2_source_backed.csv"

REQUIRED_SOURCE_FIELDS = ["source_title", "source_url", "source_locator", "evidence_note"]


def main() -> int:
    with KB_PATH.open("r", encoding="utf-8-sig", newline="") as file:
        rows = list(csv.DictReader(file))

    errors: list[str] = []
    if len(rows) != 58:
        errors.append(f"expected 58 rows, got {len(rows)}")

    ids = [row["id"] for row in rows]
    if len(ids) != len(set(ids)):
        errors.append("duplicate ids found")

    for row in rows:
        for field in REQUIRED_SOURCE_FIELDS:
            if not row.get(field, "").strip():
                errors.append(f"{row.get('id', '<missing id>')} missing {field}")
        if "待补充" not in row.get("review_status", "") and "来源支撑" not in row.get("review_status", ""):
            errors.append(f"{row.get('id', '<missing id>')} review_status does not expose source limits")

    pending_symptom_rows = sum(1 for row in rows if "待补充" in row.get("core_symptoms", ""))
    print("========== 知识库来源校验 ==========")
    print(f"文件：{KB_PATH}")
    print(f"记录数：{len(rows)}")
    print(f"临床表现待补充记录：{pending_symptom_rows}/{len(rows)}")
    print(f"来源字段：{', '.join(REQUIRED_SOURCE_FIELDS)}")

    if errors:
        print("")
        print("发现问题：")
        for error in errors:
            print("- " + error)
        return 1

    print("校验通过：记录数、唯一 ID、来源字段和审核状态均满足当前要求。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
