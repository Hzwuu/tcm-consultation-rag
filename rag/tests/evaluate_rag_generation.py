from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from tcm_agent.config import DEFAULT_DETAILS_KB_PATH
from tcm_agent.generation import GroundedRAGGenerator
from tcm_agent.knowledge_base import load_records

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def main() -> int:
    records = load_records(DEFAULT_DETAILS_KB_PATH)
    generator = GroundedRAGGenerator()
    errors: list[str] = []

    source_record = records[0]
    answer = generator.render(
        "心悸，失眠多梦，舌红少津",
        {"睡眠": ["多梦"]},
        [(source_record, 0.812)],
    )
    if "来源：" not in answer or source_record.source_title not in answer:
        errors.append("source-backed record must expose source citation")
    if "确诊" in answer or "必须服用" in answer:
        errors.append("answer contains prohibited deterministic medical advice")
    if "来源信息已登记" not in answer:
        errors.append("answer must expose source status")
    if "调理方向参考" not in answer:
        errors.append("answer must include the care-advice section")
    if "剂量" in answer:
        errors.append("answer must not contain dosage text")

    urgent = generator.render(
        "胸痛，呼吸困难",
        {},
        [(source_record, 0.812)],
    )
    if "安全分流" not in urgent or source_record.name in urgent:
        errors.append("red-flag answer must stop ordinary candidate output")

    low_confidence = generator.render(
        "有一些不舒服，但说不清楚",
        {},
        [(source_record, 0.15)],
    )
    if "信息不足" not in low_confidence or source_record.name in low_confidence:
        errors.append("low-confidence answer must avoid forcing a candidate")

    prompt = generator.build_prompt(
        "心悸，失眠多梦",
        {"睡眠": ["多梦"]},
        [(source_record, 0.812)],
    )
    for required in ["只能使用给定检索上下文", "不得输出确诊", "来源", "安全提醒"]:
        if required not in prompt:
            errors.append(f"LLM prompt missing safety instruction: {required}")

    print("========== RAG 回答生成评估 ==========")
    print(f"来源记录：{source_record.name}")
    print("来源引用、审核边界、红旗分流和 LLM 安全约束均已检查。")

    if errors:
        print("")
        print("发现问题：")
        for error in errors:
            print("- " + error)
        return 1

    print("RAG 生成评估通过。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
