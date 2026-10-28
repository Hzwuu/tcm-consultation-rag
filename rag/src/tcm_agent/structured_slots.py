from __future__ import annotations

import re
from dataclasses import dataclass

from .safety import is_negated_occurrence, normalize


SLOT_ORDER = [
    "寒热",
    "出汗",
    "口渴",
    "大便",
    "小便",
    "睡眠",
    "情绪",
    "疼痛部位",
    "持续时间",
    "严重程度",
]


@dataclass(frozen=True)
class SlotRule:
    slot: str
    value: str
    keywords: tuple[str, ...]


SLOT_RULES = [
    SlotRule("寒热", "发热", ("发热", "发烧", "身热", "高热", "低热")),
    SlotRule("寒热", "怕冷", ("怕冷", "畏寒", "恶寒", "发冷")),
    SlotRule("寒热", "潮热", ("潮热", "午后热", "五心烦热")),
    SlotRule("出汗", "自汗", ("自汗", "动一动就出汗", "白天出汗")),
    SlotRule("出汗", "盗汗", ("盗汗", "睡着出汗", "夜间出汗")),
    SlotRule("出汗", "无汗", ("无汗", "不出汗", "没汗")),
    SlotRule("出汗", "冷汗", ("冷汗", "冷汗淋漓")),
    SlotRule("口渴", "口渴", ("口渴", "想喝水", "口干")),
    SlotRule("口渴", "喜冷饮", ("想喝冷水", "喜冷饮", "喝凉水")),
    SlotRule("口渴", "不渴", ("不渴", "口不渴")),
    SlotRule("大便", "便秘", ("便秘", "大便干", "干结", "排便困难")),
    SlotRule("大便", "便溏", ("便溏", "大便稀", "拉稀", "腹泻", "泄泻")),
    SlotRule("大便", "酸臭", ("酸臭", "臭秽", "大便臭")),
    SlotRule("小便", "尿黄", ("尿黄", "小便黄", "尿色黄")),
    SlotRule("小便", "清长", ("小便清长", "尿清长", "尿清")),
    SlotRule("小便", "尿频", ("尿频", "小便频", "夜尿多")),
    SlotRule("小便", "尿痛", ("尿痛", "小便疼", "排尿疼")),
    SlotRule("睡眠", "失眠", ("失眠", "睡不着", "入睡难")),
    SlotRule("睡眠", "多梦", ("多梦", "梦多")),
    SlotRule("睡眠", "嗜睡", ("嗜睡", "犯困", "总想睡")),
    SlotRule("情绪", "烦躁易怒", ("烦躁", "易怒", "急躁", "爱发火")),
    SlotRule("情绪", "焦虑紧张", ("焦虑", "紧张", "压力大")),
    SlotRule("情绪", "思虑过度", ("想太多", "思虑", "操心")),
    SlotRule("疼痛部位", "头痛", ("头痛", "头疼")),
    SlotRule("疼痛部位", "胸痛", ("胸痛", "胸口痛")),
    SlotRule("疼痛部位", "胃脘痛", ("胃痛", "胃脘痛")),
    SlotRule("疼痛部位", "腹痛", ("腹痛", "肚子痛", "肚子疼")),
    SlotRule("疼痛部位", "胁肋痛", ("胁痛", "肋痛", "两胁痛")),
    SlotRule("疼痛部位", "腰膝酸软", ("腰膝酸软", "腰酸", "膝软")),
    SlotRule("严重程度", "剧烈", ("剧烈", "很严重", "特别严重")),
    SlotRule("严重程度", "明显", ("明显", "比较重", "加重")),
    SlotRule("严重程度", "轻微", ("轻微", "有点", "一点")),
    SlotRule("严重程度", "缓解", ("缓解", "好转", "减轻")),
]


TIME_PATTERNS = [
    re.compile(r"([0-9一二三四五六七八九十半两]+)\s*(分钟|小时|天|日|周|星期|个月|月|年)"),
    re.compile(r"(昨天|今天|前天|最近|近来|这几天|这两天|长期|多年|反复)"),
]


def extract_slots(text: str) -> dict[str, list[str]]:
    normalized = normalize(text)
    slots: dict[str, list[str]] = {slot: [] for slot in SLOT_ORDER}

    for rule in SLOT_RULES:
        for keyword in rule.keywords:
            normalized_keyword = normalize(keyword)
            if normalized_keyword in normalized and not is_slot_negated(normalized, normalized_keyword):
                add_slot_value(slots, rule.slot, rule.value)
                break

    for pattern in TIME_PATTERNS:
        for match in pattern.finditer(text):
            add_slot_value(slots, "持续时间", match.group(0))

    return {slot: values for slot, values in slots.items() if values}


def merge_slots(left: dict[str, list[str]], right: dict[str, list[str]]) -> dict[str, list[str]]:
    merged = {slot: list(values) for slot, values in left.items()}
    for slot, values in right.items():
        for value in values:
            add_slot_value(merged, slot, value)
    return merged


def add_slot_value(slots: dict[str, list[str]], slot: str, value: str) -> None:
    values = slots.setdefault(slot, [])
    if value not in values:
        values.append(value)


def is_slot_negated(text: str, keyword: str) -> bool:
    """True only when every occurrence of the keyword is negated."""
    start = 0
    found = False
    while True:
        index = text.find(keyword, start)
        if index == -1:
            return found
        found = True
        if not is_negated_occurrence(text, index):
            return False
        start = index + len(keyword)


def format_slots(slots: dict[str, list[str]]) -> str:
    parts = [
        f"{slot}：" + "、".join(slots[slot])
        for slot in SLOT_ORDER
        if slot in slots and slots[slot]
    ]
    return "；".join(parts) if parts else "暂未抽取到明确槽位"
