from __future__ import annotations

import json
import re

from .structured_slots import SLOT_ORDER, SLOT_RULES


SYSTEM_PROMPT = "你是结构化信息抽取器。只输出 JSON，不要输出任何解释、前后缀或代码块标记。"


def _allowed_values() -> dict[str, list[str]]:
    allowed: dict[str, list[str]] = {slot: [] for slot in SLOT_ORDER}
    for rule in SLOT_RULES:
        if rule.value not in allowed[rule.slot]:
            allowed[rule.slot].append(rule.value)
    return allowed


def _build_prompt(text: str) -> str:
    allowed = _allowed_values()
    lines = [
        "从下面这段患者描述中抽取结构化问诊信息。",
        "可用槽位与取值（只能使用这些取值，不要发明新取值）：",
    ]
    for slot, values in allowed.items():
        if values:
            lines.append(f"- {slot}：{'、'.join(values)}")
    lines.extend(
        [
            "",
            "输出要求：",
            '1. 只输出一个 JSON 对象，形如 {"寒热": ["发热"], "大便": ["便秘"]}；',
            "2. 没有把握或描述中没有提到的槽位不要输出；",
            "3. 否定表达（如“没有发热”“不咳嗽”）不要抽取；",
            "4. 不要输出任何解释文字。",
            "",
            f"患者描述：{text}",
        ]
    )
    return "\n".join(lines)


def _parse_json(text: str) -> dict | None:
    cleaned = text.strip()
    cleaned = re.sub(r"^```[a-zA-Z]*\s*", "", cleaned)
    cleaned = re.sub(r"\s*```$", "", cleaned)
    match = re.search(r"\{.*\}", cleaned, flags=re.S)
    if not match:
        return None
    try:
        data = json.loads(match.group(0))
    except json.JSONDecodeError:
        return None
    return data if isinstance(data, dict) else None


def extract_slots_with_llm(llm, text: str) -> tuple[dict[str, list[str]], str]:
    """Use the LLM as an optional, strictly validated slot extractor.

    Returns (slots, error). On any failure the caller keeps rule-based slots.
    """
    if not text.strip():
        return {}, "输入为空"
    if not getattr(llm, "available", False):
        return {}, "大模型不可用"

    result = llm.generate(_build_prompt(text), system_prompt=SYSTEM_PROMPT)
    if not getattr(result, "ok", False):
        return {}, getattr(result, "error", "调用失败")

    parsed = _parse_json(getattr(result, "text", ""))
    if parsed is None:
        return {}, "大模型未返回有效 JSON"

    allowed = _allowed_values()
    slots: dict[str, list[str]] = {}
    for slot, values in parsed.items():
        if slot not in allowed or not isinstance(values, list):
            continue
        kept = [str(value) for value in values if str(value) in allowed[slot]]
        if kept:
            slots[slot] = list(dict.fromkeys(kept))
    return slots, ""
