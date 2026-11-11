"""Claude mode. Masks card data, asks for structured output and checks what comes back."""

import re

import anthropic

from .masking import contains_card_data, mask
from .models import Requirement, TestDesign, Triage

DEFAULT_MODEL = "claude-opus-5-5"
# On a safety decline the API retries the same request on a fallback model.
FALLBACK_BETA = "server-side-fallback-2026-07-01"

DESIGN_SYSTEM = """You are a senior QA engineer who designs tests for payment and fintech systems.

You receive numbered requirements and a baseline test design produced by simple rules. Return the
final test design.

- Cover every requirement. Add negative, boundary and security tests where the requirement implies
  them: limits, timeouts, reversals, duplicates, idempotency, authorization and card data protection.
- Use concrete values in steps and expected results.
- Each test case references exactly one requirement ID from the input. Never invent requirement IDs.
- Number test cases TC-001, TC-002 and so on, in order.
- Report gaps: vague wording, missing acceptance criteria, untestable claims, missing error handling,
  conflicting rules. Keep baseline gaps that are valid and drop any that are wrong."""

TRIAGE_SYSTEM = """You are a payments support engineer triaging a failed card transaction from terminal,
switch and host logs. Card data has already been masked.

- Find the most likely root cause of the customer impact and list findings from most to least likely.
- Every finding cites evidence copied exactly from the log in the form "line N: <text>".
- Separate business declines (issuer codes such as 05 or 51) from system faults.
- The baseline findings come from fixed rules. Confirm, correct or extend them.
- defect_summary is a short plain text defect report: title, likely root cause, evidence, next checks."""


class AyewoError(Exception):
    pass


class ClaudeEngine:
    def __init__(self, client=None, model: str = DEFAULT_MODEL, effort: str = "high"):
        self.client = client if client is not None else anthropic.Anthropic()
        self.model = model
        self.effort = effort

    def _ask(self, system: str, prompt: str, schema):
        # Second line of defence: callers mask first, but nothing unmasked may leave this process.
        if contains_card_data(prompt):
            raise AyewoError("Refusing to send unmasked card data to the API")
        try:
            response = self.client.beta.messages.parse(
                model=self.model,
                max_tokens=16000,
                system=system,
                messages=[{"role": "user", "content": prompt}],
                output_format=schema,
                output_config={"effort": self.effort},
                betas=[FALLBACK_BETA],
                fallbacks="default",
            )
        except anthropic.AuthenticationError:
            raise AyewoError(
                "Not signed in to the Claude API. Run `ant auth login`, or set ANTHROPIC_API_KEY."
            ) from None
        except anthropic.RateLimitError:
            raise AyewoError("Rate limited by the Claude API. Wait a minute and retry.") from None
        except anthropic.APIConnectionError:
            raise AyewoError("Could not reach the Claude API. Check your connection.") from None
        except anthropic.APIStatusError as exc:
            raise AyewoError(f"Claude API error {exc.status_code}: {exc.message}") from None

        if response.stop_reason == "refusal":
            raise AyewoError("Claude declined this request. Try offline mode.")
        if response.stop_reason == "max_tokens":
            raise AyewoError("The response was cut off. Split the input into smaller files.")
        if response.parsed_output is None:
            raise AyewoError("Claude did not return structured output.")
        return response.parsed_output

    def design_tests(self, requirements: list[Requirement], baseline: TestDesign) -> TestDesign:
        listed = "\n".join(f"{r.id}: {mask(r.text).text}" for r in requirements)
        prompt = (
            f"<requirements>\n{listed}\n</requirements>\n\n"
            f"<baseline>\n{baseline.model_dump_json(indent=1)}\n</baseline>"
        )
        result: TestDesign = self._ask(DESIGN_SYSTEM, prompt, TestDesign)
        known = {r.id for r in requirements}
        result.test_cases = [t for t in result.test_cases if t.requirement_id in known]
        result.gaps = [g for g in result.gaps if g.requirement_id in known]
        return result

    def triage(self, masked_log: str, baseline: Triage) -> Triage:
        lines = {
            i: line.strip()
            for i, line in enumerate(masked_log.splitlines(), start=1)
            if line.strip()
        }
        numbered = "\n".join(f"line {i}: {text}" for i, text in lines.items())
        prompt = (
            f"<log>\n{numbered}\n</log>\n\n"
            f"<baseline>\n{baseline.model_dump_json(indent=1)}\n</baseline>"
        )
        result: Triage = self._ask(TRIAGE_SYSTEM, prompt, Triage)
        for finding in result.findings:
            finding.evidence = [e for e in finding.evidence if _cites_real_line(e, lines)]
            if not finding.evidence:
                finding.confidence = "low"
        return result


def _cites_real_line(evidence: str, lines: dict[int, str]) -> bool:
    """Keep only evidence that quotes a line that exists in the log."""
    m = re.match(r"\s*line\s+(\d+)\s*:\s*(.*)", evidence, re.I)
    if not m or int(m.group(1)) not in lines:
        return False
    quoted = m.group(2).strip()
    return bool(quoted) and (quoted in lines[int(m.group(1))] or lines[int(m.group(1))] in quoted)
