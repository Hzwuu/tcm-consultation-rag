from __future__ import annotations

import re


RED_FLAG_KEYWORDS = [
    "胸痛",
    "呼吸困难",
    "喘不过气",
    "气促",
    "意识不清",
    "昏迷",
    "呕血",
    "咯血",
    "便血",
    "黑便",
    "高热不退",
    "持续高热",
    "剧烈腹痛",
    "剧烈头痛",
    "晕厥",
    "抽搐",
    "血压很高",
    "肢体无力",
    "言语不清",
]

NEGATION_WORDS = ["没有", "无明显", "没有明显", "不是", "无", "不", "未", "否认"]

CLAUSE_DELIMITERS = "，。；、,.!?！？；:：\n"

# 这些短语里的“不/无”不是否定词，避免误伤（例如“有点不舒服，胃胀”）
NEGATION_EXCEPTIONS = (
    "不舒服",
    "不适",
    "不停",
    "不断",
    "不想",
    "不要",
    "不会",
    "不能",
    "不知",
    "不少",
    "不够",
    "无力",
)


def normalize(text: str) -> str:
    return re.sub(r"\s+", "", text.lower())


def _clause_has_negation(clause: str) -> bool:
    for phrase in NEGATION_EXCEPTIONS:
        clause = clause.replace(phrase, "")
    return any(word in clause for word in NEGATION_WORDS)


def is_negated_occurrence(text: str, index: int, window: int = 8) -> bool:
    """Whether the keyword occurrence at `index` is negated within its clause."""
    before = text[max(0, index - window) : index]
    last_delimiter = max((before.rfind(char) for char in CLAUSE_DELIMITERS), default=-1)
    clause = before[last_delimiter + 1 :]
    return _clause_has_negation(clause)


def is_negated(text: str, keyword: str) -> bool:
    """Whether EVERY occurrence of the keyword is negated.

    A single non-negated occurrence means the keyword still stands, e.g.
    “没有胸痛，但现在胸痛” must NOT be treated as negated.
    """
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


def detect_red_flags(query: str) -> list[str]:
    normalized = normalize(query)
    return [
        keyword
        for keyword in RED_FLAG_KEYWORDS
        if keyword in normalized and not is_negated(normalized, keyword)
    ]
