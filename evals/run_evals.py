"""Score Àyẹ̀wò Copilot against cases with known answers.

python evals/run_evals.py            # offline mode, free
python evals/run_evals.py --claude   # Claude mode, makes 6 API calls (costs a little)
"""

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ayewo.design import design_tests  # noqa: E402
from ayewo.llm import ClaudeEngine  # noqa: E402
from ayewo.masking import mask  # noqa: E402
from ayewo.requirements import parse_requirements  # noqa: E402
from ayewo.triage import parse_log, triage  # noqa: E402


def _plain(text: str) -> str:
    return text.replace(",", "")


def eval_design(case: dict, engine: ClaudeEngine | None) -> list[tuple[str, bool]]:
    reqs = parse_requirements(mask((ROOT / case["spec"]).read_text()).text)
    design = design_tests(reqs)
    if engine:
        design = engine.design_tests(reqs, design)
    by_req: dict[str, list] = {}
    for t in design.test_cases:
        by_req.setdefault(t.requirement_id, []).append(t)
    checks = [(f"every requirement covered ({len(reqs)})", all(r.id in by_req for r in reqs))]
    for rid, values in case["boundary_values"].items():
        text = _plain(
            " ".join(f"{t.title} {' '.join(t.steps)} {t.expected}" for t in by_req.get(rid, []))
        )
        checks.append(
            (f"{rid} boundary values {', '.join(values)}", all(v in text for v in values))
        )
    for rid in case["needs_negative"]:
        checks.append(
            (
                f"{rid} has a negative or boundary test",
                any(t.type in ("negative", "boundary") for t in by_req.get(rid, [])),
            )
        )
    for rid in case["needs_security"]:
        checks.append(
            (f"{rid} has a security test", any(t.type == "security" for t in by_req.get(rid, [])))
        )
    gaps: dict[str, set] = {}
    for g in design.gaps:
        gaps.setdefault(g.requirement_id, set()).add(g.kind)
    for rid, kinds in case["expected_gaps"].items():
        checks.append(
            (f"{rid} gap found ({' or '.join(kinds)})", bool(gaps.get(rid, set()) & set(kinds)))
        )
    for rid in case["no_gaps"]:
        checks.append((f"{rid} has no false gap", rid not in gaps))
    return checks


def eval_triage(case: dict, engine: ClaudeEngine | None) -> list[tuple[str, bool]]:
    masked = mask((ROOT / case["log"]).read_text()).text
    result = triage(parse_log(masked))
    if engine:
        result = engine.triage(masked, result)
    name = Path(case["log"]).stem
    top = result.findings[0] if result.findings else None
    categories = [f.category for f in result.findings]
    return [
        (
            f"{name}: top finding is {case['top']}",
            bool(top) and top.category == case["top"],
        ),
        (f"{name}: top finding cites evidence", bool(top) and bool(top.evidence)),
        (
            f"{name}: no wrong category ({', '.join(case['must_not'])})",
            not set(categories) & set(case["must_not"]),
        ),
    ]


def run(claude: bool = False) -> list[tuple[str, bool]]:
    cases = json.loads((ROOT / "evals" / "cases.json").read_text())
    engine = ClaudeEngine() if claude else None
    results = []
    for case in cases["design"]:
        results += eval_design(case, engine)
    for case in cases["triage"]:
        results += eval_triage(case, engine)
    return results


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--claude", action="store_true")
    parser.add_argument("--min-score", type=float, default=1.0, help="fail below this pass rate")
    args = parser.parse_args(argv)
    results = run(args.claude)
    for name, ok in results:
        print(f"{'PASS' if ok else 'FAIL'}  {name}")
    passed = sum(ok for _, ok in results)
    score = passed / len(results)
    print(
        f"\n{'claude' if args.claude else 'offline'} mode: {passed}/{len(results)} checks passed ({score:.0%})"
    )
    return 0 if score >= args.min_score else 1


if __name__ == "__main__":
    sys.exit(main())
