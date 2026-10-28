from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Record:
    id: str = ""
    name: str = ""
    category: str = ""
    core_symptoms: str = ""
    tongue_pulse: str = ""
    differentiation_points: str = ""
    common_triggers: str = ""
    follow_up_questions: str = ""
    care_advice: str = ""
    diet_advice: str = ""
    lifestyle_advice: str = ""
    prescription_reference: str = ""
    contraindications: str = ""
    red_flags: str = ""
    retrieval_keywords: str = ""
    source_note: str = ""
    review_status: str = ""
    last_updated: str = ""
    source_title: str = ""
    source_url: str = ""
    source_locator: str = ""
    evidence_note: str = ""

    @property
    def retrieval_text(self) -> str:
        return "；".join(
            [
                self.name,
                self.category,
                self.core_symptoms,
                self.differentiation_points,
                self.common_triggers,
                self.retrieval_keywords,
            ]
        )
