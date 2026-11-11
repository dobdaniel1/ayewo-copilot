"""Offline test design: rule-based test cases and requirement gap checks."""

import re
from decimal import Decimal, InvalidOperation

from .models import Gap, Requirement, TestCase, TestDesign

_NUM = r"(\d[\d,]*(?:\.\d+)?)"
_BETWEEN = re.compile(
    rf"\bbetween\s+[^\d]{{0,6}}{_NUM}\s*(?:\w+\s+)?and\s+[^\d]{{0,6}}{_NUM}", re.I
)
_MIN = re.compile(
    rf"\b(?:at least|minimum(?: of)?|no less than|not less than|min\.?)\s+[^\d]{{0,6}}{_NUM}", re.I
)
_MAX = re.compile(
    rf"\b(?:at most|maximum(?: of)?|up to|no more than|not more than|not exceed(?:ing)?|max\.?)"
    rf"\s+[^\d]{{0,6}}{_NUM}",
    re.I,
)
_LENGTH = re.compile(r"\b(?:exactly\s+)?(\d{1,3})[- ](?:digit|character|char)s?\b", re.I)
_WITHIN = re.compile(
    r"\bwithin\s+(\d+(?:\.\d+)?)\s*(ms|milliseconds?|seconds?|secs?|s|minutes?|mins?)\b", re.I
)

_NEGATIVE = re.compile(
    r"\b(must not|shall not|should not|cannot|can't|only|reject\w*|declin\w*|invalid|unless|"
    r"not (?:be )?allowed|prevent\w*|block\w*|deny|denied|duplicate)\b",
    re.I,
)
_INPUT = re.compile(
    r"\b(enter(?:s|ed)?|submit\w*|request\w*|upload\w*|fields?|amounts?|inputs?|forms?|send\w*|pay\w*)\b",
    re.I,
)
_SECURITY = re.compile(
    r"\b(pan|card ?number|pin|cvv|password|token|otp|authenticat\w*|authori[sz]\w*|role|"
    r"permission\w*|encrypt\w*|mask\w*|audit\w*|session|pci|log(?:s|ged|ging)?)\b",
    re.I,
)
_MONEY = re.compile(
    r"\b(amount|naira|ngn|usd|balance|fee|limit|refund|settle\w*|payment)\b|[$₦]", re.I
)

_VAGUE = re.compile(
    r"\b(fast|quick(?:ly)?|user[- ]friendly|easy|easily|appropriate(?:ly)?|adequate(?:ly)?|robust|"
    r"efficient(?:ly)?|flexible|intuitive|seamless(?:ly)?|as needed|as required|etc\.?|minimal|"
    r"sufficient|reasonable|timely|good|properly|correctly|normal(?:ly)?)\b",
    re.I,
)
_PERFORMANCE = re.compile(
    r"\b(fast|quick(?:ly)?|performance|response time|responsive|timely|load|scal\w+|latency)\b",
    re.I,
)
_HAS_NUMBER = re.compile(r"\d")
_ABSOLUTE = re.compile(r"\b(always|never|100%|all times|any circumstances|every time)\b", re.I)
_TBD = re.compile(r"\b(TBD|TBC|to be (?:decided|confirmed|defined))\b|\?\?", re.I)


def _num(raw: str) -> Decimal | None:
    try:
        return Decimal(raw.replace(",", ""))
    except InvalidOperation:  # pragma: no cover - regex only passes numeric text
        return None


def _step(value: Decimal) -> Decimal:
    exponent = value.as_tuple().exponent
    return Decimal(1).scaleb(exponent) if isinstance(exponent, int) and exponent < 0 else Decimal(1)


def _fmt(value: Decimal) -> str:
    return f"{value:,}" if value == value.to_integral() else f"{value:,.2f}"


class _Builder:
    def __init__(self):
        self.cases: list[TestCase] = []

    def add(
        self,
        req: Requirement,
        kind: str,
        title: str,
        steps: list[str],
        expected: str,
        priority: str = "medium",
        preconditions: list[str] | None = None,
    ) -> None:
        self.cases.append(
            TestCase(
                id=f"TC-{len(self.cases) + 1:03d}",
                requirement_id=req.id,
                title=title,
                type=kind,
                priority=priority,
                preconditions=preconditions or [f"System configured as described in {req.id}"],
                steps=steps,
                expected=expected,
            )
        )


def _boundaries(req: Requirement) -> list[tuple[str, str, bool]]:
    """(label, value, accepted) tuples for numeric limits found in the requirement."""
    text = req.text
    points: list[tuple[str, str, bool]] = []
    if m := _BETWEEN.search(text):
        low, high = _num(m.group(1)), _num(m.group(2))
        step = min(_step(low), _step(high))
        points += [
            ("just below minimum", _fmt(low - step), False),
            ("minimum", _fmt(low), True),
            ("maximum", _fmt(high), True),
            ("just above maximum", _fmt(high + step), False),
        ]
    else:
        if m := _MIN.search(text):
            low = _num(m.group(1))
            points += [
                ("just below minimum", _fmt(low - _step(low)), False),
                ("minimum", _fmt(low), True),
            ]
        if m := _MAX.search(text):
            high = _num(m.group(1))
            points += [
                ("maximum", _fmt(high), True),
                ("just above maximum", _fmt(high + _step(high)), False),
            ]
    if m := _LENGTH.search(text):
        n = int(m.group(1))
        points += [
            (f"{n - 1} characters", f"length {n - 1}", False),
            (f"{n} characters", f"length {n}", True),
            (f"{n + 1} characters", f"length {n + 1}", False),
        ]
    return points


def design_tests(requirements: list[Requirement]) -> TestDesign:
    b = _Builder()
    for req in requirements:
        money = bool(_MONEY.search(req.text))
        b.add(
            req,
            "positive",
            f"Happy path: {req.text}",
            [
                f"Prepare valid data for {req.id}",
                f"Perform the action: {req.text}",
                "Record the result",
            ],
            f"The system behaves exactly as {req.id} states",
            priority="high",
        )
        for label, value, accepted in _boundaries(req):
            outcome = (
                "accepted and processed"
                if accepted
                else "rejected with a clear error, no side effects"
            )
            b.add(
                req,
                "boundary",
                f"Boundary {label}: {value}",
                [f"Use the value {value}", f"Perform the action in {req.id}"],
                f"Value {value} is {outcome}",
                priority="high" if money else "medium",
            )
        if m := _WITHIN.search(req.text):
            limit = f"{m.group(1)} {m.group(2)}"
            b.add(
                req,
                "boundary",
                f"Timing at the {limit} limit",
                [
                    f"Measure the action in {req.id} under normal load",
                    f"Repeat with the dependency slowed to just over {limit}",
                ],
                f"Completes within {limit} normally; the over-limit case follows the timeout path "
                "(error shown, no partial update, reversal or retry as specified)",
                priority="high",
            )
        if _NEGATIVE.search(req.text) or _INPUT.search(req.text):
            b.add(
                req,
                "negative",
                f"Invalid or disallowed input for {req.id}",
                [
                    "Use input that breaks the rule (missing, malformed, wrong type, not permitted)",
                    f"Perform the action in {req.id}",
                ],
                "Request is rejected with a specific error; no data is changed; the attempt is logged",
            )
        if _SECURITY.search(req.text):
            b.add(
                req,
                "security",
                f"Security check for {req.id}",
                [
                    "Perform the action as an unauthorised or wrong-role user",
                    "Inspect responses, logs and stored data for sensitive values",
                ],
                "Unauthorised access is denied; card data, PINs and secrets never appear in clear in "
                "responses, logs or storage",
                priority="high",
            )
    return TestDesign(test_cases=b.cases, gaps=find_gaps(requirements))


def find_gaps(requirements: list[Requirement]) -> list[Gap]:
    gaps: list[Gap] = []
    for req in requirements:
        text = req.text
        if m := _TBD.search(text):
            gaps.append(
                Gap(
                    requirement_id=req.id,
                    kind="incomplete",
                    issue=f"Contains placeholder '{m.group(0)}'",
                    suggestion="Resolve the open item before test design is signed off",
                )
            )
        vague = {w.lower() for w in _VAGUE.findall(text)}
        if _PERFORMANCE.search(text) and not _HAS_NUMBER.search(text):
            gaps.append(
                Gap(
                    requirement_id=req.id,
                    kind="missing_acceptance_criteria",
                    issue="Performance expectation without a measurable target",
                    suggestion="State a number, for example 'p95 response under 2 seconds at "
                    "50 transactions per second'",
                )
            )
            vague -= {"fast", "quick", "quickly", "timely"}  # already reported above
        if vague:
            vague = sorted(vague)
            gaps.append(
                Gap(
                    requirement_id=req.id,
                    kind="ambiguous",
                    issue=f"Vague wording: {', '.join(vague)}",
                    suggestion="Replace with observable, measurable behaviour",
                )
            )
        if re.search(r"\band/or\b", text, re.I):
            gaps.append(
                Gap(
                    requirement_id=req.id,
                    kind="ambiguous",
                    issue="'and/or' leaves it unclear whether both conditions are required",
                    suggestion="Split into separate requirements or state the exact rule",
                )
            )
        if _ABSOLUTE.search(text) and not re.search(r"\b(shall|must) (not|never)\b", text, re.I):
            gaps.append(
                Gap(
                    requirement_id=req.id,
                    kind="untestable",
                    issue="Absolute claim that cannot be proven by testing",
                    suggestion="Define a measurable target, for example availability of 99.9% "
                    "per month",
                )
            )
        if re.search(r"\bshould\b", text, re.I) and not re.search(r"\b(shall|must)\b", text, re.I):
            gaps.append(
                Gap(
                    requirement_id=req.id,
                    kind="ambiguous",
                    issue="'should' makes it unclear whether this is mandatory",
                    suggestion="Use 'must' for mandatory behaviour, or mark it as optional",
                )
            )
    return gaps
