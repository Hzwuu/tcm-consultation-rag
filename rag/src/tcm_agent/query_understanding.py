from __future__ import annotations

import re
from dataclasses import dataclass
from functools import lru_cache

from .safety import is_negated_occurrence, normalize


# canonical symptom -> accepted variants (including common colloquial expressions)
SYNONYM_GROUPS: dict[str, tuple[str, ...]] = {
    "发热": ("发热", "发烧", "身热", "高热", "低热", "低烧", "体温高"),
    "怕冷": ("怕冷", "畏寒", "恶寒", "发冷", "怕风", "手脚发凉", "手脚冰凉"),
    "咽痛": ("咽痛", "喉咙痛", "嗓子疼", "喉咙疼", "喉咙红痛", "咽喉痛", "咽干痛"),
    "咳嗽": ("咳嗽", "干咳", "咳痰", "咳白稀痰", "咳"),
    "痰多": ("痰多", "痰多色白", "痰中带血", "黄痰", "白痰"),
    "流鼻涕": ("流鼻涕", "流涕", "鼻涕", "鼻塞", "流清鼻涕", "流清鼻子", "流黄浓鼻涕"),
    "口渴": ("口渴", "口干", "想喝水", "咽干", "口干咽燥"),
    "喜冷饮": ("想喝冷水", "喜冷饮", "喝凉水", "爱喝冷饮", "口渴想喝凉水"),
    "不渴": ("不渴", "不想喝水", "口不渴"),
    "便秘": ("便秘", "大便干", "大便干结", "干结", "排便困难"),
    "腹泻": ("腹泻", "拉稀", "拉肚子", "便溏", "大便稀", "大便稀溏", "泄泻"),
    "大便酸臭": ("大便酸臭", "酸臭", "大便臭", "臭秽", "大便酸臭"),
    "失眠": ("失眠", "睡不着", "入睡难", "多梦易醒", "心烦失眠", "睡眠不好", "睡眠不太好", "睡不好", "睡不踏实"),
    "多梦": ("多梦", "梦多"),
    "心烦": ("心烦", "烦躁", "烦燥", "易怒", "急躁", "爱发火"),
    "乏力": ("乏力", "没力气", "浑身乏力", "疲倦", "疲劳", "神疲乏力", "少气懒言", "容易累", "白天容易累", "容易疲劳"),
    "头晕": ("头晕", "眩晕", "头晕眼花", "头重脚轻", "头晕目眩"),
    "头痛": ("头痛", "头疼", "头目胀痛"),
    "胃胀": ("胃胀", "腹胀", "肚子胀", "脘腹胀", "饭后腹胀", "腹胀恶心"),
    "胃痛": ("胃痛", "胃脘痛", "胃部灼痛", "胃部隐痛", "胃里烧灼", "胃有烧灼感", "烧灼感"),
    "反酸": ("反酸", "泛酸", "烧心", "嗳腐吞酸", "打嗝有酸腐味", "打嗝酸腐", "打嗝有酸味"),
    "食欲不振": ("不想吃饭", "食欲不振", "纳差", "食欲差", "食欲不佳"),
    "腰膝酸软": ("腰酸", "腰膝酸软", "腰膝酸痛", "膝软", "腰疼", "腰痛", "腰膝冷痛"),
    "盗汗": ("盗汗", "夜间出汗", "睡着出汗"),
    "自汗": ("自汗", "白天出汗", "动一动就出汗", "容易出汗"),
    "无汗": ("无汗", "不出汗", "没汗", "没有汗"),
    "畏寒肢冷": ("畏寒肢冷", "四肢不温", "肢体不温", "手脚发冷", "手足不温"),
    "夜尿多": ("夜尿多", "夜尿频", "小便清长", "尿清长"),
    "尿黄": ("尿黄", "小便黄", "尿色黄", "小便短黄"),
    "口苦": ("口苦",),
    "口臭": ("口臭",),
    "心慌": ("心慌", "心悸"),
    "胸闷": ("胸闷", "胸痛", "胸口痛", "胸胁胀", "两胁胀痛", "胸闷胁胀", "胁痛", "两胁痛", "胸闷胁痛"),
    "关节痛": ("关节痛", "关节疼痛", "关节酸楚", "遇冷加重", "阴雨天加重"),
    "潮热": ("潮热", "五心烦热", "手足心热", "手脚心发热", "手脚心热"),
    "气短": ("气短", "气促", "喘不过气", "活动后加重", "咳嗽无力"),
    "健忘": ("健忘", "记性差", "记忆力差"),
    "面色苍白": ("面色苍白", "面色萎黄", "面色暗沉", "口唇紫暗", "脸色差", "面色差"),
    "大便黏腻": ("大便黏腻", "大便黏", "大便粘"),
    "痰湿身重": ("身体沉重", "身重", "头身困重"),
}

_SYNONYM_LOOKUP: dict[str, str] = {}
for _canonical, _variants in SYNONYM_GROUPS.items():
    _SYNONYM_LOOKUP[_canonical] = _canonical
    for _variant in _variants:
        _SYNONYM_LOOKUP[_variant] = _canonical

_VOCABULARY: tuple[str, ...] = tuple(sorted(_SYNONYM_LOOKUP, key=len, reverse=True))

_PROTECTED_PHRASES = (
    "不清楚",
    "说不清",
    "说不明白",
    "没有明显",
    "不明显",
    "没有",
    "不是",
    "不想",
    "不要",
    "不知道",
    "不确定",
    "不舒",
    "无明确",
    "无明显",
)

_STOPWORDS = (
    "正常",
    "太多",
    "烧烤",
    "胃口",
    "一般",
    "还好",
    "还行",
    "还可以",
    "睡眠",
    "白天",
    "晚上",
    "昨天",
    "今天",
    "最近",
    "开始",
    "以后",
    "时候",
    "现在",
    "感觉",
    "有点",
    "比较",
    "特别",
    "一直",
    "然后",
    "还是",
    "就是",
    "这个",
    "那个",
    "可能",
    "可以",
    "已经",
    "不好",
    "不太",
)


@dataclass(frozen=True)
class QueryAnalysis:
    original: str
    normalized: str
    corrected: str
    terms: list[str]
    corrections: list[str]

    def term_text(self) -> str:
        return "、".join(self.terms) if self.terms else "未识别到明确症状"

    def correction_text(self) -> str:
        return "、".join(self.corrections) if self.corrections else "无"


def canonical_variants(term: str) -> tuple[str, ...]:
    return SYNONYM_GROUPS.get(term, (term,))


def levenshtein(left: str, right: str, max_distance: int = 2) -> int:
    if abs(len(left) - len(right)) > max_distance:
        return max_distance + 1
    previous = list(range(len(right) + 1))
    for i, left_char in enumerate(left, start=1):
        current = [i]
        for j, right_char in enumerate(right, start=1):
            current.append(
                min(
                    previous[j] + 1,
                    current[j - 1] + 1,
                    previous[j - 1] + (left_char != right_char),
                )
            )
        previous = current
    return previous[-1]


def _contains_known_term(text: str) -> bool:
    return any(term in text for term in _SYNONYM_LOOKUP)


def _overlaps_stopword(run_text: str, start: int, end: int) -> bool:
    for word in _STOPWORDS:
        search_from = 0
        while True:
            index = run_text.find(word, search_from)
            if index == -1:
                break
            if not (end <= index or start >= index + len(word)):
                return True
            search_from = index + len(word)
    return False


@lru_cache(maxsize=512)
def _nearest_term(window: str) -> str | None:
    same_length: list[str] = []
    other_length: list[str] = []
    for term in _VOCABULARY:
        if not (set(window) & set(term)):
            continue
        distance = levenshtein(window, term, max_distance=1)
        if distance > 1:
            continue
        if len(term) == len(window):
            same_length.append(term)
        elif abs(len(term) - len(window)) == 1 and not (
            term.startswith(window) or term.endswith(window)
        ):
            # A longer term that merely starts or ends with the window is a
            # completion (e.g. 嗓子 -> 嗓子疼), not a typo. Skip those.
            other_length.append(term)
    if same_length:
        return min(same_length, key=lambda term: levenshtein(window, term, 1))
    if other_length:
        return min(other_length, key=lambda term: levenshtein(window, term, 1))
    return None


def correct_typos(text: str, max_corrections: int = 2) -> tuple[str, list[str]]:
    """Correct very small typos only inside phrases with no known symptom term."""
    corrected = text
    corrections: list[str] = []

    for _ in range(max_corrections):
        changed = False
        for run in re.finditer(r"[\u4e00-\u9fff]+", corrected):
            run_text = run.group(0)
            if _contains_known_term(run_text):
                continue
            if any(phrase in run_text for phrase in _PROTECTED_PHRASES):
                continue
            for length in (2, 3, 4):
                if length > len(run_text):
                    break
                for offset in range(len(run_text) - length + 1):
                    window = run_text[offset : offset + length]
                    if window in _SYNONYM_LOOKUP:
                        continue
                    if _overlaps_stopword(run_text, offset, offset + length):
                        continue
                    candidate = _nearest_term(window)
                    if candidate is None:
                        continue
                    start = run.start() + offset
                    corrected = corrected[:start] + candidate + corrected[start + length :]
                    corrections.append(f"{window}→{candidate}")
                    changed = True
                    break
                if changed:
                    break
            if changed:
                break
        if not changed:
            break

    return corrected, corrections


def detect_terms(text: str) -> list[str]:
    normalized = normalize(text)
    occupied: list[tuple[int, int]] = []
    found: dict[str, int] = {}

    for term in _VOCABULARY:
        start = 0
        while True:
            index = normalized.find(term, start)
            if index == -1:
                break
            end = index + len(term)
            if not any(not (end <= left or index >= right) for left, right in occupied):
                occupied.append((index, end))
                if not is_negated_occurrence(normalized, index):
                    canonical = _SYNONYM_LOOKUP[term]
                    if canonical not in found or index < found[canonical]:
                        found[canonical] = index
            start = index + len(term)

    return [term for term, _position in sorted(found.items(), key=lambda item: item[1])]


def analyze_query(text: str) -> QueryAnalysis:
    normalized = normalize(text)
    corrected, corrections = correct_typos(normalized)
    terms = detect_terms(corrected)
    return QueryAnalysis(
        original=text,
        normalized=normalized,
        corrected=corrected,
        terms=terms,
        corrections=corrections,
    )
