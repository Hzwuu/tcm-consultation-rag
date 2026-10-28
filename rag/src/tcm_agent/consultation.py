from __future__ import annotations

from dataclasses import dataclass, field

from .embedding_retrieval import VectorSearchIndex
from .generation import GroundedRAGGenerator
from .llm_slots import extract_slots_with_llm
from .models import Record
from .query_understanding import analyze_query
from .retrieval import retrieve
from .safety import detect_red_flags
from .structured_slots import extract_slots, format_slots, merge_slots


GENERAL_QUESTIONS = [
    "症状大概持续多久了？是突然出现，还是慢慢加重？",
    "有没有发热、怕冷、出汗、口渴这些表现？",
    "大便和小便最近有什么变化？",
    "睡眠、食欲、情绪最近怎么样？",
]


@dataclass
class ConsultationState:
    initial_description: str = ""
    answers: list[tuple[str, str]] = field(default_factory=list)
    red_flags: list[str] = field(default_factory=list)
    asked_questions: set[str] = field(default_factory=set)
    slots: dict[str, list[str]] = field(default_factory=dict)
    query_terms: list[str] = field(default_factory=list)
    corrections: list[str] = field(default_factory=list)
    turn_count: int = 0
    slot_source: str = "rules"
    slot_error: str = ""

    def combined_text(self) -> str:
        parts = [self.initial_description]
        parts.extend(f"{question} {answer}" for question, answer in self.answers)
        return "；".join(part for part in parts if part.strip())

    def add_answer(
        self,
        question: str,
        answer: str,
        llm=None,
        use_llm_slots: bool = False,
    ) -> None:
        self.answers.append((question, answer))
        self.turn_count += 1
        self.asked_questions.add(question)
        self.red_flags = sorted(set(self.red_flags + detect_red_flags(answer)))
        self.slots = merge_slots(self.slots, extract_slots(answer))
        self.maybe_extract_llm_slots(answer, llm, use_llm_slots)
        analysis = analyze_query(answer)
        self.query_terms = merge_unique(self.query_terms, analysis.terms)
        self.corrections = merge_unique(self.corrections, analysis.corrections)

    def maybe_extract_llm_slots(self, text: str, llm, use_llm_slots: bool) -> None:
        """Optionally enrich rule-based slots with an LLM extractor."""
        if not use_llm_slots or llm is None:
            return
        llm_slots, error = extract_slots_with_llm(llm, text)
        if llm_slots:
            self.slots = merge_slots(self.slots, llm_slots)
            self.slot_source = "rules+llm"
        elif error:
            self.slot_error = error


class TCMConsultAgent:
    def __init__(
        self,
        records: list[Record],
        max_turns: int = 4,
        retrieval_mode: str = "tfidf",
    ) -> None:
        self.records = records
        self.max_turns = max_turns
        self.retrieval_mode = retrieval_mode
        self.vector_index = (
            VectorSearchIndex.build(records)
            if retrieval_mode == "embedding"
            else None
        )

    def start(
        self,
        initial_description: str,
        llm=None,
        use_llm_slots: bool = False,
    ) -> ConsultationState:
        state = ConsultationState(initial_description=initial_description.strip())
        state.red_flags = detect_red_flags(state.initial_description)
        state.slots = extract_slots(state.initial_description)
        state.maybe_extract_llm_slots(state.initial_description, llm, use_llm_slots)
        analysis = analyze_query(state.initial_description)
        state.query_terms = analysis.terms
        state.corrections = analysis.corrections
        return state

    def current_matches(self, state: ConsultationState) -> list[tuple[Record, float]]:
        if self.vector_index is not None:
            return self.vector_index.search(state.combined_text(), top_k=3)
        return retrieve(self.records, state.combined_text(), top_k=3)

    def should_stop(self, state: ConsultationState) -> bool:
        return bool(state.red_flags) or state.turn_count >= self.max_turns

    def next_question(self, state: ConsultationState) -> str | None:
        if self.should_stop(state):
            return None

        candidate_questions: list[str] = []
        for record, _score in self.current_matches(state)[:2]:
            candidate_questions.extend(split_questions(record.follow_up_questions))
        candidate_questions.extend(GENERAL_QUESTIONS)

        for question in candidate_questions:
            question = question.strip()
            if question and question not in state.asked_questions:
                return question
        return None

    def summary(self, state: ConsultationState, llm=None) -> str:
        rendered = GroundedRAGGenerator().render_with_llm(
            state.combined_text(),
            state.slots,
            self.current_matches(state),
            llm=llm,
            known_names=[record.name for record in self.records],
        )
        lines: list[str] = []
        lines.append("========== 中医问诊辅助报告 ==========")
        lines.append(
            "识别到的症状："
            + ("、".join(state.query_terms) if state.query_terms else "未识别到明确症状")
        )
        lines.append(
            "术语纠正：" + ("、".join(state.corrections) if state.corrections else "无")
        )
        if state.slot_source == "rules+llm":
            lines.append("槽位抽取：规则 + 大模型增强")
        elif state.slot_error:
            lines.append(f"槽位抽取：规则（大模型增强失败：{state.slot_error}）")
        lines.append("")
        lines.append(rendered.text)
        if rendered.note:
            lines.append("")
            lines.append(f"【生成方式】{rendered.note}")
        return "\n".join(lines)

    def rag_prompt(self, state: ConsultationState) -> str:
        return GroundedRAGGenerator().build_prompt(
            state.combined_text(),
            state.slots,
            self.current_matches(state),
        )


def split_questions(text: str) -> list[str]:
    return [part.strip() for part in text.replace("？", "?").split("?") if part.strip()]


def merge_unique(left: list[str], right: list[str]) -> list[str]:
    merged = list(left)
    for item in right:
        if item not in merged:
            merged.append(item)
    return merged
