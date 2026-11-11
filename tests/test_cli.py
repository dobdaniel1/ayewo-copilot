import csv
import io
import json

import pytest

from ayewo import cli
from ayewo.models import Triage


def run(capsys, *args):
    code = cli.main(list(args))
    out = capsys.readouterr()
    return code, out.out, out.err


def test_testcases_markdown(capsys, spec_path):
    code, out, _ = run(capsys, "testcases", str(spec_path))
    assert code == 0
    assert "Mode: offline | Requirements: 14" in out
    assert "## Requirement gaps" in out
    assert "Not covered" not in out


def test_testcases_csv_and_json(capsys, spec_path):
    _, out, _ = run(capsys, "testcases", str(spec_path), "-f", "csv")
    rows = list(csv.DictReader(io.StringIO(out)))
    assert rows[0]["ID"] == "TC-001" and rows[0]["Steps"].startswith("1. ")
    _, out, _ = run(capsys, "testcases", str(spec_path), "-f", "json")
    data = json.loads(out)
    assert data["mode"] == "offline" and len(data["requirements"]) == 14


def test_write_to_file(capsys, spec_path, tmp_path):
    target = tmp_path / "tests.csv"
    code, out, err = run(capsys, "testcases", str(spec_path), "-f", "csv", "-o", str(target))
    assert code == 0 and out == "" and "wrote" in err
    assert target.read_text().startswith("ID,Requirement")


def test_errors(capsys, tmp_path):
    empty = tmp_path / "empty.md"
    empty.write_text("# Nothing here\n")
    code, _, err = run(capsys, "testcases", str(empty))
    assert code == 1 and "No requirements" in err
    code, _, err = run(capsys, "triage", str(tmp_path / "missing.log"))
    assert code == 1 and "error:" in err


def test_spec_card_numbers_masked_everywhere(capsys, tmp_path):
    spec = tmp_path / "spec.md"
    spec.write_text("- REQ-001: Test card 4111111111111111 must be approved.\n")
    for fmt in ("md", "csv", "json"):
        _, out, _ = run(capsys, "testcases", str(spec), "-f", fmt)
        assert "4111111111111111" not in out
        assert "411111******1111" in out


def test_triage_markdown_masks_card_data(capsys, log_path):
    code, out, _ = run(capsys, "triage", str(log_path("terminal_host_mismatch")))
    assert code == 0
    assert "### 1. terminal_host_mismatch (high confidence)" in out
    assert "Card data items masked: 1" in out
    assert "5555555555554444" not in out


def test_triage_multiple_files_json(capsys, log_path):
    _, out, _ = run(
        capsys,
        "triage",
        str(log_path("issuer_decline")),
        str(log_path("duplicate_stan")),
        "-f",
        "json",
    )
    data = json.loads(out)
    assert data["source"] == "issuer_decline.log, duplicate_stan.log"
    assert {f["category"] for f in data["findings"]} >= {"issuer_decline", "duplicate_transmission"}


def test_mask_command(capsys, log_path):
    _, out, _ = run(capsys, "mask", str(log_path("timeout_no_reversal")))
    assert out.startswith("# masked: 1 PAN")
    assert "4111111111111111" not in out


class FakeEngine:
    def design_tests(self, requirements, baseline):
        return baseline

    def triage(self, masked_log, baseline):
        assert "4111111111111111" not in masked_log
        return Triage(findings=baseline.findings[:1], defect_summary="from claude")


@pytest.fixture
def fake_engine(monkeypatch):
    monkeypatch.setattr(cli, "_engine", lambda args: FakeEngine())


def test_claude_mode_is_labelled(capsys, fake_engine, spec_path, log_path):
    _, out, _ = run(capsys, "testcases", str(spec_path), "--claude")
    assert "Mode: claude" in out
    _, out, _ = run(
        capsys, "triage", str(log_path("timeout_no_reversal")), "--claude", "-f", "json"
    )
    data = json.loads(out)
    assert data["mode"] == "claude" and data["defect_summary"] == "from claude"


def test_engine_factory_uses_options(monkeypatch):
    seen = {}
    monkeypatch.setattr(cli, "ClaudeEngine", lambda **kw: seen.update(kw))
    args = cli.build_parser().parse_args(["triage", "x.log", "--claude", "--effort", "max"])
    cli._engine(args)
    assert seen == {"model": "claude-opus-5-5", "effort": "max"}
