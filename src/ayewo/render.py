import csv
import io
from collections import Counter

from .models import TestDesignReport, TriageReport


def design_markdown(report: TestDesignReport) -> str:
    covered = Counter(t.requirement_id for t in report.test_cases)
    types = Counter(t.type for t in report.test_cases)
    out = [
        f"# Test design: {report.source}",
        "",
        f"Mode: {report.mode} | Requirements: {len(report.requirements)} | "
        f"Test cases: {len(report.test_cases)} | Gaps: {len(report.gaps)}",
        "",
        "Test types: " + ", ".join(f"{k} {v}" for k, v in sorted(types.items())),
        "",
        "## Traceability",
        "",
        "| Requirement | Tests | Text |",
        "|---|---|---|",
    ]
    for r in report.requirements:
        ids = ", ".join(t.id for t in report.test_cases if t.requirement_id == r.id) or "**none**"
        out.append(f"| {r.id} | {ids} | {_cell(r.text)} |")
    uncovered = [r.id for r in report.requirements if not covered[r.id]]
    if uncovered:
        out += ["", f"Not covered: {', '.join(uncovered)}"]
    out += ["", "## Test cases", ""]
    for t in report.test_cases:
        out += [
            f"### {t.id} ({t.requirement_id}, {t.type}, {t.priority})",
            "",
            t.title,
            "",
            "Preconditions: " + "; ".join(t.preconditions),
            "",
            *[f"{i}. {s}" for i, s in enumerate(t.steps, start=1)],
            "",
            f"Expected: {t.expected}",
            "",
        ]
    out += ["## Requirement gaps", ""]
    if report.gaps:
        out += ["| Requirement | Kind | Issue | Suggestion |", "|---|---|---|---|"]
        out += [
            f"| {g.requirement_id} | {g.kind} | {_cell(g.issue)} | {_cell(g.suggestion)} |"
            for g in report.gaps
        ]
    else:
        out.append("None found.")
    return "\n".join(out) + "\n"


def design_csv(report: TestDesignReport) -> str:
    buf = io.StringIO()
    writer = csv.writer(buf, lineterminator="\n")
    writer.writerow(
        ["ID", "Requirement", "Type", "Priority", "Title", "Preconditions", "Steps", "Expected"]
    )
    for t in report.test_cases:
        writer.writerow(
            [
                t.id,
                t.requirement_id,
                t.type,
                t.priority,
                t.title,
                "\n".join(t.preconditions),
                "\n".join(f"{i}. {s}" for i, s in enumerate(t.steps, start=1)),
                t.expected,
            ]
        )
    return buf.getvalue()


def triage_markdown(report: TriageReport) -> str:
    out = [
        f"# Triage: {report.source}",
        "",
        f"Mode: {report.mode} | Log lines: {len(report.timeline)} | Card data items masked: "
        f"{report.masked_items}",
        "",
        "## Findings",
        "",
    ]
    for n, f in enumerate(report.findings, start=1):
        out += [f"### {n}. {f.category} ({f.confidence} confidence)", "", f.root_cause, ""]
        if f.evidence:
            out += ["Evidence:", "", "```", *f.evidence, "```", ""]
        out += ["Next checks:", "", *[f"- {c}" for c in f.next_checks], ""]
    out += [
        "## Timeline",
        "",
        "| Line | Time | Source | STAN | MTI | RC | Event |",
        "|---|---|---|---|---|---|---|",
    ]
    for e in report.timeline:
        out.append(
            f"| {e.line} | {e.timestamp or ''} | {e.source or ''} | {e.stan or ''} | {e.mti or ''} | "
            f"{e.response_code or ''} | {_cell(e.text)} |"
        )
    out += ["", "## Defect summary", "", "```", report.defect_summary, "```"]
    return "\n".join(out) + "\n"


def _cell(text: str) -> str:
    return text.replace("|", "\\|").replace("\n", " ")
