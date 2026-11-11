import pytest

from ayewo.masking import mask
from ayewo.triage import parse_log, triage


def run(text):
    return triage(parse_log(mask(text).text))


@pytest.mark.parametrize(
    "name,top",
    [
        ("timeout_no_reversal", "timeout_without_reversal"),
        ("terminal_host_mismatch", "terminal_host_mismatch"),
        ("duplicate_stan", "duplicate_transmission"),
        ("host_down_failover", "host_unavailable"),
        ("issuer_decline", "issuer_decline"),
    ],
)
def test_example_logs_top_finding(log_path, name, top):
    result = run(log_path(name).read_text())
    assert result.findings[0].category == top
    assert result.findings[0].evidence
    assert top.replace("_", " ") in result.defect_summary.lower()


def test_issuer_decline_is_not_a_system_fault(log_path):
    categories = {f.category for f in run(log_path("issuer_decline").read_text()).findings}
    assert categories == {"issuer_decline"}


def test_rc_only_outage_is_medium_confidence(log_path):
    findings = run(log_path("timeout_no_reversal").read_text()).findings
    assert next(f for f in findings if f.category == "host_unavailable").confidence == "medium"
    host_down = run(log_path("host_down_failover").read_text()).findings[0]
    assert host_down.confidence == "high"


def test_parse_log_fields():
    (event,) = parse_log(
        "2026-11-11 10:00:00.5 [Switch] mti=0200 request sent stan=000001 rrn=631500000001 rc=00 amount=100"
    )
    assert event.timestamp == "2026-11-11 10:00:00.5"
    assert event.source == "switch"
    assert (event.stan, event.rrn, event.mti, event.response_code, event.amount) == (
        "000001",
        "631500000001",
        "0200",
        "00",
        "100",
    )


def test_bare_mti_with_keyword_and_lines_without_stan():
    events = parse_log("10:00:00 0210 response received\nno stan on this line\n\n")
    assert events[0].mti == "0210" and events[0].timestamp == "10:00:00"
    assert len(events) == 2


def test_late_response_and_unacknowledged_reversal():
    log = """\
mti=0200 request sent stan=000010 amount=500
stan=000010 timed out
mti=0420 reversal sent stan=000010 amount=500
mti=0210 response received stan=000010 rc=00 amount=500
"""
    categories = [f.category for f in run(log).findings]
    assert "late_response" in categories
    assert "reversal_unacknowledged" in categories
    assert "timeout_without_reversal" not in categories


def test_acknowledged_reversal_is_clean():
    log = "mti=0400 reversal sent stan=000011\nstan=000011 reversal accepted rc=00\n"
    assert "reversal_unacknowledged" not in [f.category for f in run(log).findings]


def test_rc_68_counts_as_late():
    assert run("stan=000012 rc=68 late response").findings[0].category == "late_response"


def test_amount_mismatch():
    log = "mti=0200 request sent stan=000013 amount=1000\nmti=0210 response received stan=000013 amount=100\n"
    assert run(log).findings[0].category == "amount_mismatch"


def test_no_known_pattern():
    result = run("[switch] heartbeat ok\n")
    assert result.findings[0].category == "no_known_pattern"
    assert result.findings[0].confidence == "low"
    assert "Title: No known pattern" in result.defect_summary
