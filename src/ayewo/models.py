"""Data shapes shared by offline mode, Claude mode and the renderers."""

from typing import Literal

from pydantic import BaseModel, Field

TestType = Literal["positive", "negative", "boundary", "security"]
Priority = Literal["high", "medium", "low"]
GapKind = Literal["ambiguous", "missing_acceptance_criteria", "untestable", "incomplete"]
Confidence = Literal["high", "medium", "low"]
Category = Literal[
    "timeout_without_reversal",
    "reversal_unacknowledged",
    "late_response",
    "terminal_host_mismatch",
    "duplicate_transmission",
    "host_unavailable",
    "issuer_decline",
    "amount_mismatch",
    "configuration_error",
    "other",
    "no_known_pattern",
]


class Requirement(BaseModel):
    id: str
    text: str
    line: int


class TestCase(BaseModel):
    __test__ = False  # not a pytest test class

    id: str
    requirement_id: str
    title: str
    type: TestType
    priority: Priority
    preconditions: list[str] = Field(default_factory=list)
    steps: list[str]
    expected: str


class Gap(BaseModel):
    requirement_id: str
    kind: GapKind
    issue: str
    suggestion: str


class TestDesign(BaseModel):
    """What Claude must return for test design. Mirrors the offline output."""

    __test__ = False  # not a pytest test class

    test_cases: list[TestCase]
    gaps: list[Gap]


class TestDesignReport(TestDesign):
    mode: Literal["offline", "claude"]
    source: str
    requirements: list[Requirement]


class LogEvent(BaseModel):
    line: int
    timestamp: str | None
    source: str | None
    stan: str | None
    rrn: str | None
    mti: str | None
    response_code: str | None
    amount: str | None = None
    text: str


class Finding(BaseModel):
    category: Category
    root_cause: str
    confidence: Confidence
    evidence: list[str] = Field(description="Exact log lines that support the finding")
    next_checks: list[str]


class Triage(BaseModel):
    """What Claude must return for triage."""

    findings: list[Finding]
    defect_summary: str


class TriageReport(Triage):
    mode: Literal["offline", "claude"]
    source: str
    masked_items: int
    timeline: list[LogEvent]
