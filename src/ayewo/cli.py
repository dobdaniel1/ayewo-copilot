import argparse
import sys
from pathlib import Path

from .design import design_tests
from .llm import DEFAULT_MODEL, AyewoError, ClaudeEngine
from .masking import mask
from .models import TestDesignReport, TriageReport
from .render import design_csv, design_markdown, triage_markdown
from .requirements import parse_requirements
from .triage import parse_log, triage


def _engine(args) -> ClaudeEngine:
    return ClaudeEngine(model=args.model, effort=args.effort)


def run_testcases(args) -> str:
    path = Path(args.spec)
    # Mask on read so card numbers in examples never reach reports or the API.
    requirements = parse_requirements(mask(path.read_text(encoding="utf-8")).text)
    if not requirements:
        raise AyewoError(
            f"No requirements found in {path}. Use IDs like REQ-001 or 'shall' bullets."
        )
    design = design_tests(requirements)
    mode = "offline"
    if args.claude:
        design = _engine(args).design_tests(requirements, design)
        mode = "claude"
    report = TestDesignReport(
        mode=mode, source=path.name, requirements=requirements, **design.model_dump()
    )
    if args.format == "csv":
        return design_csv(report)
    if args.format == "json":
        return report.model_dump_json(indent=2) + "\n"
    return design_markdown(report)


def run_triage(args) -> str:
    raw = "\n".join(Path(p).read_text(encoding="utf-8") for p in args.logs)
    masked = mask(raw)
    events = parse_log(masked.text)
    result = triage(events)
    mode = "offline"
    if args.claude:
        result = _engine(args).triage(masked.text, result)
        mode = "claude"
    report = TriageReport(
        mode=mode,
        source=", ".join(Path(p).name for p in args.logs),
        masked_items=masked.total,
        timeline=events,
        **result.model_dump(),
    )
    if args.format == "json":
        return report.model_dump_json(indent=2) + "\n"
    return triage_markdown(report)


def run_mask(args) -> str:
    result = mask(Path(args.file).read_text(encoding="utf-8"))
    note = (
        f"# masked: {result.pans} PAN, {result.track2} track 2, {result.pin_blocks} PIN block, "
        f"{result.cvvs} CVV\n"
    )
    return note + result.text + ("" if result.text.endswith("\n") else "\n")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ayewo",
        description="Àyẹ̀wò Copilot: test design and transaction triage for payment systems. Offline by default; "
        "add --claude for Claude-assisted results.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    def claude_options(p):
        p.add_argument("--claude", action="store_true", help="use Claude (needs `ant auth login`)")
        p.add_argument("--model", default=DEFAULT_MODEL)
        p.add_argument(
            "--effort", default="high", choices=["low", "medium", "high", "xhigh", "max"]
        )
        p.add_argument("-o", "--out", help="write to a file instead of stdout")

    t = sub.add_parser(
        "testcases", help="generate traceable test cases and a gap report from a spec"
    )
    t.add_argument("spec")
    t.add_argument("-f", "--format", choices=["md", "csv", "json"], default="md")
    claude_options(t)
    t.set_defaults(func=run_testcases)

    r = sub.add_parser("triage", help="find the likely root cause of a failed transaction")
    r.add_argument("logs", nargs="+")
    r.add_argument("-f", "--format", choices=["md", "json"], default="md")
    claude_options(r)
    r.set_defaults(func=run_triage)

    m = sub.add_parser(
        "mask", help="show a file with card data masked, exactly as Claude would see it"
    )
    m.add_argument("file")
    m.add_argument("-o", "--out")
    m.set_defaults(func=run_mask)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        output = args.func(args)
    except (AyewoError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    if args.out:
        Path(args.out).write_text(output, encoding="utf-8")
        print(f"wrote {args.out}", file=sys.stderr)
    else:
        sys.stdout.write(output)
    return 0


if __name__ == "__main__":
    sys.exit(main())
