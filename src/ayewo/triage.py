"""Offline triage: parse transaction logs and apply known payment failure patterns."""

import re
from collections import defaultdict

from .models import Finding, LogEvent, Triage
from .response_codes import ISSUER_DECLINES, SYSTEM_FAILURES, meaning

_TS = re.compile(
    r"(\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}(?:[.,]\d+)?|\b\d{2}:\d{2}:\d{2}(?:[.,]\d+)?)"
)
_SOURCE = re.compile(r"\[([A-Za-z][\w -]{1,30})\]")
_STAN = re.compile(r"\bstan[=: ]+(\d{6})\b", re.I)
_RRN = re.compile(r"\brrn[=: ]+(\w{12})\b", re.I)
_MTI = re.compile(
    r"\bmti[=: ]+(\d{4})\b|\b(0[1-8][0-3]0)\b(?=\s+(?:request|response|advice|reversal|sent|received|msg))",
    re.I,
)
_RC = re.compile(
    r"\b(?:rc|resp(?:onse)?[ _]?code|f39|field[ _]?39|de39)[=: ]+([0-9A-Z]{2})\b", re.I
)
_AMOUNT = re.compile(r"\bamount[=: ]+(\d+(?:\.\d+)?)\b", re.I)

_TIMEOUT = re.compile(r"\b(time[d ]?out|timed out|no response)\b", re.I)
_REVERSAL = re.compile(r"\breversal\b", re.I)
_REVERSAL_ACK = re.compile(
    r"\breversal\b.*\b(ack\w*|accepted|approved|confirmed|response|rc[=: ]+00)\b", re.I
)
_CONNECTION = re.compile(
    r"\b(connection (?:refused|reset|failed|error)|unreachable|host down|connect failed|socket error|"
    r"no route to host)\b",
    re.I,
)
_LATE = re.compile(r"\b(late response|response after timeout|arrived after)\b", re.I)
_TERMINAL_FAIL = re.compile(r"\b(declined|failed|failure|error|cancel+ed)\b", re.I)
_TERMINAL_OK = re.compile(r"\b(approved|success\w*)\b", re.I)

REQUESTS = {"0100", "0200"}
RESPONSES = {"0110", "0210"}
REVERSALS = {"0400", "0420"}
REVERSAL_RESPONSES = {"0410", "0430"}


def parse_log(text: str) -> list[LogEvent]:
    events = []
    for line_no, line in enumerate(text.splitlines(), start=1):
        if not line.strip():
            continue
        mti = _MTI.search(line)
        events.append(
            LogEvent(
                line=line_no,
                timestamp=(m.group(1) if (m := _TS.search(line)) else None),
                source=(m.group(1).strip().lower() if (m := _SOURCE.search(line)) else None),
                stan=(m.group(1) if (m := _STAN.search(line)) else None),
                rrn=(m.group(1) if (m := _RRN.search(line)) else None),
                mti=(mti.group(1) or mti.group(2)) if mti else None,
                response_code=(m.group(1).upper() if (m := _RC.search(line)) else None),
                amount=(m.group(1) if (m := _AMOUNT.search(line)) else None),
                text=line.strip(),
            )
        )
    return events


def _quote(events: list[LogEvent], limit: int = 4) -> list[str]:
    return [f"line {e.line}: {e.text}" for e in events[:limit]]


def _is_terminal(e: LogEvent) -> bool:
    return bool(e.source) and any(k in e.source for k in ("terminal", "pos", "atm", "app"))


def _group(events: list[LogEvent]) -> dict[str, list[LogEvent]]:
    groups: dict[str, list[LogEvent]] = defaultdict(list)
    current = None
    for e in events:
        # Lines without a STAN belong to the transaction logged just before them.
        current = e.stan or current
        groups[current or "unknown"].append(e)
    return groups


def _rules_for(stan: str, ev: list[LogEvent]) -> list[Finding]:
    found: list[Finding] = []
    label = f"STAN {stan}" if stan != "unknown" else "this transaction"
    requests = [e for e in ev if e.mti in REQUESTS]
    responses = [e for e in ev if e.mti in RESPONSES]
    timeouts = [e for e in ev if _TIMEOUT.search(e.text)]
    reversals = [
        e
        for e in ev
        if e.mti in REVERSALS or (_REVERSAL.search(e.text) and not _REVERSAL_ACK.search(e.text))
    ]
    reversal_acks = [e for e in ev if e.mti in REVERSAL_RESPONSES or _REVERSAL_ACK.search(e.text)]
    codes = [e for e in ev if e.response_code]

    if requests and timeouts and not reversals:
        found.append(
            Finding(
                category="timeout_without_reversal",
                root_cause=f"The request for {label} timed out and no reversal was sent. The issuer may have "
                "approved and debited the customer while the terminal reported a failure.",
                confidence="high",
                evidence=_quote(requests[:1] + timeouts),
                next_checks=[
                    "Confirm at the issuer or switch whether the authorization was approved",
                    "Check why the timeout path did not trigger a 0400/0420 reversal",
                    "If approved at the issuer, raise a reversal or refund and check reconciliation",
                ],
            )
        )
    if reversals and not reversal_acks:
        found.append(
            Finding(
                category="reversal_unacknowledged",
                root_cause=f"A reversal was sent for {label} but no acknowledgement was logged, so the "
                "original debit may still stand.",
                confidence="medium",
                evidence=_quote(reversals),
                next_checks=[
                    "Check the store and forward queue for the pending reversal",
                    "Confirm the reversal reached the issuer (0410/0430 response)",
                ],
            )
        )
    late = [e for e in ev if _LATE.search(e.text) or e.response_code == "68"]
    if timeouts and responses and any(r.line > timeouts[0].line for r in responses):
        late += [r for r in responses if r.line > timeouts[0].line]
    if late:
        found.append(
            Finding(
                category="late_response",
                root_cause=f"The host response for {label} arrived after the timeout, so the terminal and the "
                "host may disagree on the outcome.",
                confidence="high",
                evidence=_quote(timeouts[:1] + late),
                next_checks=[
                    "Compare host latency with the terminal and switch timeout settings",
                    "Make sure late approvals are reversed automatically",
                ],
            )
        )
    host_ok = [e for e in codes if e.response_code == "00" and not _is_terminal(e)]
    terminal_fail = [
        e
        for e in ev
        if _is_terminal(e) and _TERMINAL_FAIL.search(e.text) and not _TERMINAL_OK.search(e.text)
    ]
    if host_ok and terminal_fail:
        found.append(
            Finding(
                category="terminal_host_mismatch",
                root_cause=f"The host approved {label} (response 00) but the terminal reported a failure. "
                "The customer may be charged for a transaction they think failed.",
                confidence="high",
                evidence=_quote(host_ok[:1] + terminal_fail),
                next_checks=[
                    "Check the terminal's handling of the 0210 response (parsing, MAC, timeout)",
                    "Reverse or refund the approved transaction and flag it for reconciliation",
                ],
            )
        )
    rrns = {e.rrn for e in ev if e.rrn}
    if len(requests) > 1 or len(rrns) > 1:
        found.append(
            Finding(
                category="duplicate_transmission",
                root_cause=f"{label} was sent more than once"
                + (f" with {len(rrns)} different RRNs" if len(rrns) > 1 else "")
                + ". A retry without idempotency can charge the customer twice.",
                confidence="medium",
                evidence=_quote(requests or [e for e in ev if e.rrn]),
                next_checks=[
                    "Check that duplicates are detected by terminal ID, STAN and date",
                    "Confirm only one debit exists at the issuer",
                ],
            )
        )
    conn = [e for e in ev if _CONNECTION.search(e.text)]
    system = [e for e in codes if e.response_code in SYSTEM_FAILURES - {"68"}]
    if conn or system:
        code_text = ", ".join(
            sorted({f"{e.response_code} ({meaning(e.response_code)})" for e in system})
        )
        found.append(
            Finding(
                category="host_unavailable",
                root_cause=f"The issuer host or switch was unavailable for {label}"
                + (f"; response {code_text}" if code_text else "")
                + ".",
                # A 91 alone can be the switch's own reply after a timeout, so it is weaker evidence.
                confidence="high" if conn else "medium",
                evidence=_quote(conn + system),
                next_checks=[
                    "Check host connectivity and health at the logged time",
                    "Confirm the routing table has a fallback host for this BIN and that failover ran",
                ],
            )
        )
    declines = [e for e in codes if e.response_code in ISSUER_DECLINES]
    if declines:
        code = declines[-1].response_code
        found.append(
            Finding(
                category="issuer_decline",
                root_cause=f"The issuer declined {label} with {code} ({meaning(code)}). This is a business "
                "decline, not a system fault.",
                confidence="high",
                evidence=_quote(declines),
                next_checks=[
                    "Confirm the terminal showed the correct message to the cardholder",
                    "No system fix needed unless the decline itself is wrong",
                ],
            )
        )
    amounts = {e.amount for e in ev if e.amount and (e.mti in REQUESTS | RESPONSES | REVERSALS)}
    if len(amounts) > 1:
        found.append(
            Finding(
                category="amount_mismatch",
                root_cause=f"Messages for {label} carry different amounts ({', '.join(sorted(amounts))}).",
                confidence="high",
                evidence=_quote([e for e in ev if e.amount]),
                next_checks=[
                    "Compare field 4 across request, response and reversal",
                    "Check currency and minor unit handling between terminal and switch",
                ],
            )
        )
    return found


_SEVERITY = {
    "timeout_without_reversal": 0,
    "terminal_host_mismatch": 1,
    "amount_mismatch": 2,
    "late_response": 3,
    "reversal_unacknowledged": 4,
    "duplicate_transmission": 5,
    "host_unavailable": 6,
    "issuer_decline": 7,
}


def triage(events: list[LogEvent]) -> Triage:
    findings: list[Finding] = []
    for stan, group in _group(events).items():
        findings += _rules_for(stan, group)
    findings.sort(key=lambda f: _SEVERITY.get(f.category, 99))
    if not findings:
        findings = [
            Finding(
                category="no_known_pattern",
                root_cause="No known failure pattern matched these logs.",
                confidence="low",
                evidence=[],
                next_checks=[
                    "Add terminal, switch and host logs for the same STAN and time window",
                    "Run with --claude for a deeper read of unusual failures",
                ],
            )
        ]
    return Triage(findings=findings, defect_summary=defect_summary(findings[0], events))


def defect_summary(top: Finding, events: list[LogEvent]) -> str:
    stans = sorted({e.stan for e in events if e.stan})
    rrns = sorted({e.rrn for e in events if e.rrn})
    lines = [
        f"Title: {top.category.replace('_', ' ').capitalize()}"
        + (f" for STAN {', '.join(stans)}" if stans else ""),
        "",
        f"Root cause (likely): {top.root_cause}",
        f"Confidence: {top.confidence}",
    ]
    if rrns:
        lines.append(f"RRN: {', '.join(rrns)}")
    if top.evidence:
        lines += ["", "Evidence:"] + [f"- {e}" for e in top.evidence]
    lines += ["", "Next checks:"] + [f"- {c}" for c in top.next_checks]
    return "\n".join(lines)
