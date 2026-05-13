from __future__ import annotations

from .openai_intake import (
    IntakeResult,
    IntakeStructuredOutput,
    MediatorBrief,
    MediatorBriefStructuredOutput,
    OpenAIIntakeService,
    generate_mediator_brief,
    process_report_intake,
)

AIIntakeService = OpenAIIntakeService

__all__ = [
    "AIIntakeService",
    "OpenAIIntakeService",
    "IntakeResult",
    "IntakeStructuredOutput",
    "MediatorBrief",
    "MediatorBriefStructuredOutput",
    "process_report_intake",
    "generate_mediator_brief",
]
