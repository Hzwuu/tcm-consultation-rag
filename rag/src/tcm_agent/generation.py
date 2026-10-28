from __future__ import annotations

import re
from dataclasses import dataclass

from .models import Record
from .safety import detect_red_flags
from .structured_slots import format_slots


PENDING_MARKERS = ("待补充", "待专业审核", "待中医专业审核")
PRESCRIPTION_DISCLAIMER = "仅为传统知识参考，不可自行服用；使用须经执业医师指导。"


def display_review_status(value: str | None) -> str:
    value = (value or "").strip()
    if "安全优先" in value:
        return "安全优先"
    if not value or "待" in value or "未登记" in value:
        return "来源信息已登记"
    return value


@dataclass(frozen=True)
class LLMRenderResult:
    text: str
    used_llm: bool
    note: str = ""


@dataclass(frozen=True)
class GroundedRAGGenerator:
    """Generate a deterministic, source-aware answer from retrieved records.

    This is the safe local baseline for the optional LLM generator. It never
    adds medical facts outside the retrieved records.
    """

    max_candidates: int = 3
    min_confidence: float = 0.2

    def render(
        self,
        initial_text: str,
        slots: dict[str, list[str]],
        matches: list[tuple[Record, float]],
    ) -> str:
        red_flags = detect_red_flags(initial_text)
        if red_flags:
            return self._render_red_flags(red_flags)

        lines = [
            "【中医问诊辅助报告】（非诊断结论）",
            "",
            "一、问诊信息汇总",
            initial_text.strip() or "（未填写）",
            "",
            "二、结构化信息",
            format_slots(slots),
            "",
        ]

        if not matches or self._is_low_confidence(matches):
            lines.extend(
                [
                    "三、候选方向",
                    "当前信息不足或检索匹配度较低，系统不强行给出候选证型。",
                    "建议补充症状的起始时间、寒热、出汗、饮食和二便变化；症状持续或加重时请线下就医。",
                    "",
                    "四、安全提醒",
                    "本报告不提供诊断与处方，不替代线下医生诊断；如出现胸痛、呼吸困难、呕血、黑便、持续高热等情况，请及时线下就医。",
                    "",
                    "五、免责声明",
                    "本报告仅基于当前检索到的知识库记录，用于学习和问诊辅助，不是诊断结论。",
                ]
            )
            return "\n".join(lines)

        candidates = matches[: self.max_candidates]
        lines.append("三、候选方向（按检索相关度排序）")
        for index, (record, score) in enumerate(candidates, start=1):
            lines.append(f"{index}. {record.name}（{record.category}，检索相关度 {score:.3f}）")
            lines.append(f"   依据：{self._evidence(record)}")
            lines.append(f"   来源：{self._source(record)}")
            source_status = (
                display_review_status(record.review_status)
                if record.source_title or record.source_url
                else "基础演示记录"
            )
            lines.append(f"   来源状态：{source_status}")

            questions = self._questions(record.follow_up_questions)
            if questions:
                lines.append(f"   建议追问：{'；'.join(questions[:3])}")
        lines.append("")

        lines.append("四、调理方向参考（治法层面，须经专业审核后执行）")
        care_lines = self._care_lines(candidates)
        lines.extend(care_lines or ["当前检索记录中暂无可直接输出的调理参考。"])
        lines.append("")

        lines.append("五、传统知识参考（方剂名称）")
        prescription_lines = self._prescription_lines(candidates)
        lines.extend(prescription_lines or ["当前检索记录中暂无可展示的方剂参考。"])
        lines.append("")

        lines.extend(
            [
                "六、安全提醒",
                "本报告不提供诊断与处方，不替代线下医生诊断；如出现胸痛、呼吸困难、呕血、黑便、持续高热等情况，请及时线下就医。",
                "",
                "七、免责声明",
                "本报告仅基于当前检索到的知识库记录，用于学习和问诊辅助，不是诊断结论；来源与审核信息见各候选条目。",
            ]
        )
        return "\n".join(lines)

    def build_prompt(
        self,
        initial_text: str,
        slots: dict[str, list[str]],
        matches: list[tuple[Record, float]],
    ) -> str:
        """Build a strict prompt for the LLM renderer without calling an API."""
        context_lines = []
        for index, (record, score) in enumerate(matches[: self.max_candidates], start=1):
            context_lines.append(
                "\n".join(
                    [
                        f"[候选{index}] {record.name} | category={record.category} | score={score:.3f}",
                        f"evidence={self._evidence(record)}",
                        f"source={self._source(record)}",
                        f"review_status={record.review_status or '未登记'}",
                        f"care={self._compact(record.care_advice, record.diet_advice, record.lifestyle_advice)}",
                        f"prescription_reference={self._compact(record.prescription_reference)}",
                        f"follow_up={record.follow_up_questions or '待补充'}",
                    ]
                )
            )

        return "\n".join(
            [
                "你是中医健康咨询辅助系统的回答生成器。",
                "只能使用给定检索上下文，不得补充上下文之外的医学事实。",
                "不得输出确诊、必须服用某方、用法用量（包括任何剂量数字）或自行购药建议。",
                "方剂只能以“传统知识参考”列出名称，并必须注明“不可自行服用，须经执业医师指导”。",
                "方剂名称只能来自检索上下文；检索上下文未提供方剂时，必须写明“当前检索记录中未提供方剂参考”，不得自行补充其他方剂。",
                "只能提及检索上下文中出现的证型名称，不得自行推断其他证型。",
                "如果检测到红旗症状，只输出及时线下就医的安全分流。",
                "请按“候选方向、依据、来源、建议追问、调理方向参考、传统知识参考（方剂）、安全提醒”的结构输出。",
                "如果最高检索相关度低于可信阈值，不要强行选择候选证型，应提示信息不足。",
                f"用户原始描述：{initial_text}",
                f"结构化槽位：{format_slots(slots)}",
                "检索上下文：",
                "\n\n".join(context_lines) or "无",
            ]
        )

    def render_with_llm(
        self,
        initial_text: str,
        slots: dict[str, list[str]],
        matches: list[tuple[Record, float]],
        llm=None,
        known_names: list[str] | None = None,
    ) -> LLMRenderResult:
        """Render the structured report, preferring the optional LLM.

        The deterministic local template is always kept as the fallback, and
        LLM output must pass the safety filter and the citation check.
        """
        red_flags = detect_red_flags(initial_text)
        if red_flags:
            return LLMRenderResult(
                self._render_red_flags(red_flags),
                False,
                "检测到红旗症状：未调用大模型，优先安全分流",
            )

        if not matches or self._is_low_confidence(matches):
            return LLMRenderResult(
                self.render(initial_text, slots, matches),
                False,
                "信息不足或匹配度低：未调用大模型",
            )

        if llm is None:
            return LLMRenderResult(
                self.render(initial_text, slots, matches),
                False,
                "未启用大模型：使用本地模板",
            )

        prompt = self.build_prompt(initial_text, slots, matches)
        result = llm.generate(prompt)
        if not getattr(result, "ok", False):
            reason = getattr(result, "error", "调用失败")
            return LLMRenderResult(
                self.render(initial_text, slots, matches),
                False,
                f"大模型不可用，已回退本地模板（{reason}）",
            )

        text = (getattr(result, "text", "") or "").strip()
        violation = self.check_safety(text)
        if violation:
            return LLMRenderResult(
                self.render(initial_text, slots, matches),
                False,
                f"大模型输出触发安全过滤（{violation}），已回退本地模板",
            )

        citation = self.check_citations(text, matches, known_names)
        if citation:
            retry_prompt = (
                prompt
                + "\n\n【引用校验提示】你上一次的回答提到了检索上下文之外的证型（"
                + citation
                + "）。请重新输出完整回答，只使用检索上下文中出现的证型名称。"
            )
            retry_result = llm.generate(retry_prompt)
            if getattr(retry_result, "ok", False):
                retry_text = (getattr(retry_result, "text", "") or "").strip()
                if not self.check_safety(retry_text) and not self.check_citations(
                    retry_text, matches, known_names
                ):
                    model = getattr(retry_result, "model", "") or getattr(result, "model", "")
                    footer = (
                        f"\n\n（本报告由大模型 {model or ''} 基于上述检索记录生成，"
                        "仅作学习参考，不是诊断结论。）"
                    )
                    return LLMRenderResult(
                        retry_text + footer,
                        True,
                        f"大模型：{model or '已启用'}（引用校验重试后通过）",
                    )
            return LLMRenderResult(
                self.render(initial_text, slots, matches),
                False,
                f"大模型引用了检索上下文之外的证型（{citation}），重试后仍未通过，已回退本地模板",
            )

        model = getattr(result, "model", "")
        footer = (
            f"\n\n（本报告由大模型 {model or ''} 基于上述检索记录生成，"
            "仅作学习参考，不是诊断结论。）"
        )
        return LLMRenderResult(text + footer, True, f"大模型：{model or '已启用'}")

    @staticmethod
    def check_safety(text: str) -> str:
        patterns = (
            re.compile(r"确诊为"),
            re.compile(r"必须服用"),
            re.compile(r"(?<!不)(?<!避免)(?<!禁止)(建议|可以|请)你?服用"),
            re.compile(r"剂量为"),
            re.compile(r"\d+\s*(mg|毫克)"),
            re.compile(r"自行购买"),
        )
        for pattern in patterns:
            match = pattern.search(text)
            if match:
                return match.group(0)
        return ""

    @staticmethod
    def check_citations(
        text: str,
        matches: list[tuple[Record, float]],
        known_names: list[str] | None = None,
    ) -> str:
        """Return the first syndrome mentioned outside the retrieved set."""
        if not known_names:
            return ""

        allowed = {record.name for record, _score in matches}
        allowed_spans: list[tuple[int, int]] = []
        for name in allowed:
            start = 0
            while True:
                index = text.find(name, start)
                if index == -1:
                    break
                allowed_spans.append((index, index + len(name)))
                start = index + 1

        for name in known_names:
            if not name or name in allowed:
                continue
            start = 0
            while True:
                index = text.find(name, start)
                if index == -1:
                    break
                end = index + len(name)
                covered = any(left <= index and end <= right for left, right in allowed_spans)
                if not covered:
                    return name
                start = index + 1
        return ""

    def _is_low_confidence(self, matches: list[tuple[Record, float]]) -> bool:
        return not matches or matches[0][1] < self.min_confidence

    @staticmethod
    def _render_red_flags(red_flags: list[str]) -> str:
        return "\n".join(
            [
                "【安全分流】",
                "检测到红旗症状：" + "、".join(red_flags),
                "请及时线下就医或咨询专业医生。本系统停止输出普通证候解释、调理建议和方剂信息。",
            ]
        )

    @staticmethod
    def _evidence(record: Record) -> str:
        fields = [record.core_symptoms, record.differentiation_points]
        usable = [field for field in fields if field and not any(marker in field for marker in PENDING_MARKERS)]
        return "；".join(usable) if usable else "当前记录没有可直接输出的已审核临床证据"

    @staticmethod
    def _source(record: Record) -> str:
        if record.source_title and record.source_url:
            locator = f"（{record.source_locator}）" if record.source_locator else ""
            return f"{record.source_title}{locator}：{record.source_url}"
        return "当前记录未登记可追溯来源，不作为默认医疗建议"

    @staticmethod
    def _compact(*fields: str) -> str:
        values = [
            field.strip()
            for field in fields
            if field and field.strip() and not any(marker in field for marker in PENDING_MARKERS)
        ]
        return "；".join(values) if values else "待补充"

    @staticmethod
    def _care_lines(candidates: list[tuple[Record, float]]) -> list[str]:
        lines: list[str] = []
        for record, _score in candidates:
            for field in (record.care_advice, record.diet_advice, record.lifestyle_advice):
                value = (field or "").strip()
                if value and not any(marker in value for marker in PENDING_MARKERS):
                    item = f"- {value}"
                    if item not in lines:
                        lines.append(item)
        return lines[:6]

    @staticmethod
    def _prescription_lines(candidates: list[tuple[Record, float]]) -> list[str]:
        lines: list[str] = []
        for record, _score in candidates:
            value = (record.prescription_reference or "").strip()
            if value and not any(marker in value for marker in PENDING_MARKERS):
                item = f"- {record.name}：{value}（{PRESCRIPTION_DISCLAIMER}）"
                if item not in lines:
                    lines.append(item)
        return lines[:3]

    @staticmethod
    def _questions(text: str) -> list[str]:
        if not text or any(marker in text for marker in PENDING_MARKERS):
            return []
        return [part.strip() for part in text.replace("？", "?").split("?") if part.strip()]
