from types import SimpleNamespace

import anthropic
import httpx2
import pytest

from ayewo.design import design_tests
from ayewo.llm import DEFAULT_MODEL, FALLBACK_BETA, AyewoError, ClaudeEngine
from ayewo.masking import mask
from ayewo.models import Finding, Gap, Requirement, TestCase, TestDesign, Triage
from ayewo.triage import parse_log, triage


class FakeMessages:
    def __init__(self, parsed=None, stop_reason="end_turn", error=None):
        self.parsed, self.stop_reason, self.error = parsed, stop_reason, error
        self.calls = []

    def parse(self, **kwargs):
        self.calls.append(kwargs)
        if self.error:
            raise self.error
        return SimpleNamespace(parsed_output=self.parsed, stop_reason=self.stop_reason)


def engine(**kwargs):
    messages = FakeMessages(**kwargs)
    client = SimpleNamespace(beta=SimpleNamespace(messages=messages))
    return ClaudeEngine(client=client), messages


REQS = [Requirement(id="REQ-001", text="Mask PAN 4111111111111111 in logs.", line=1)]


def case(rid):
    return TestCase(
        id="TC-001",
        requirement_id=rid,
        title="t",
        type="positive",
        priority="high",
        steps=["s"],
        expected="e",
    )


def test_design_request_shape_and_masking():
    reply = TestDesign(
        test_cases=[case("REQ-001"), case("REQ-404")],
        gaps=[Gap(requirement_id="REQ-404", kind="ambiguous", issue="i", suggestion="s")],
    )
    eng, messages = engine(parsed=reply)
    masked_reqs = [r.model_copy(update={"text": mask(r.text).text}) for r in REQS]
    # The engine masks requirement text itself even if the caller forgot.
    result = eng.design_tests(REQS, design_tests(masked_reqs))

    call = messages.calls[0]
    assert call["model"] == DEFAULT_MODEL == "claude-opus-5-5"
    assert call["output_format"] is TestDesign
    assert call["output_config"] == {"effort": "high"}
    assert call["betas"] == [FALLBACK_BETA] and call["fallbacks"] == "default"
    prompt = call["messages"][0]["content"]
    assert "4111111111111111" not in prompt and "411111******1111" in prompt
    # Invented requirement IDs are dropped.
    assert [t.requirement_id for t in result.test_cases] == ["REQ-001"]
    assert result.gaps == []


LOG = "mti=0200 request sent stan=000001\nstan=000001 timed out\n"


def finding(evidence):
    return Finding(
        category="other", root_cause="r", confidence="high", evidence=evidence, next_checks=["n"]
    )


def test_triage_keeps_only_real_evidence():
    masked = mask(LOG).text
    reply = Triage(
        findings=[
            finding(
                ["line 2: stan=000001 timed out", "line 9: invented", "line 1: something else"]
            ),
            finding(["no line number at all"]),
        ],
        defect_summary="d",
    )
    eng, messages = engine(parsed=reply)
    result = eng.triage(masked, triage(parse_log(masked)))
    assert (
        "line 1: mti=0200 request sent stan=000001" in messages.calls[0]["messages"][0]["content"]
    )
    assert messages.calls[0]["output_format"] is Triage
    assert result.findings[0].evidence == ["line 2: stan=000001 timed out"]
    assert result.findings[0].confidence == "high"
    assert result.findings[1].evidence == [] and result.findings[1].confidence == "low"


def test_refuses_unmasked_baseline():
    eng, messages = engine(parsed=None)
    with pytest.raises(AyewoError, match="unmasked"):
        eng.design_tests(REQS, design_tests(REQS))
    assert messages.calls == []


def test_refuses_to_send_unmasked_card_data():
    eng, messages = engine(parsed=None)
    with pytest.raises(AyewoError, match="unmasked"):
        eng.triage("pan=4111111111111111", Triage(findings=[], defect_summary=""))
    assert messages.calls == []


@pytest.mark.parametrize(
    "stop_reason,parsed,message",
    [
        ("refusal", None, "declined"),
        ("max_tokens", None, "cut off"),
        ("end_turn", None, "structured"),
    ],
)
def test_bad_stops(stop_reason, parsed, message):
    eng, _ = engine(parsed=parsed, stop_reason=stop_reason)
    with pytest.raises(AyewoError, match=message):
        eng.triage(LOG, Triage(findings=[], defect_summary=""))


REQUEST = httpx2.Request("POST", "https://api.anthropic.com/v1/messages")


def status_error(cls, code):
    return cls("boom", response=httpx2.Response(code, request=REQUEST), body=None)


@pytest.mark.parametrize(
    "error,message",
    [
        (status_error(anthropic.AuthenticationError, 401), "ant auth login"),
        (status_error(anthropic.RateLimitError, 429), "Rate limited"),
        (anthropic.APIConnectionError(request=REQUEST), "Could not reach"),
        (status_error(anthropic.InternalServerError, 500), "error 500"),
    ],
)
def test_api_errors_become_friendly(error, message):
    eng, _ = engine(error=error)
    with pytest.raises(AyewoError, match=message):
        eng.design_tests(REQS[:0], TestDesign(test_cases=[], gaps=[]))


def test_default_client_is_constructed(monkeypatch):
    monkeypatch.setattr(anthropic, "Anthropic", lambda: "client")
    assert ClaudeEngine().client == "client"
