import pytest

from ayewo.design import design_tests, find_gaps
from ayewo.models import Requirement


def req(text, rid="REQ-001"):
    return Requirement(id=rid, text=text, line=1)


def titles(design, kind):
    return [t.title for t in design.test_cases if t.type == kind]


def test_every_requirement_gets_a_positive_case():
    design = design_tests(
        [req("The system shall export reports.", f"REQ-00{i}") for i in range(1, 4)]
    )
    assert [t.requirement_id for t in design.test_cases if t.type == "positive"] == [
        "REQ-001",
        "REQ-002",
        "REQ-003",
    ]
    assert [t.id for t in design.test_cases] == ["TC-001", "TC-002", "TC-003"]


def test_between_range_boundaries_with_decimals():
    design = design_tests([req("Amounts must be between 1.00 and 5,000.00 NGN.")])
    assert titles(design, "boundary") == [
        "Boundary just below minimum: 0.99",
        "Boundary minimum: 1.00",
        "Boundary maximum: 5,000.00",
        "Boundary just above maximum: 5,000.01",
    ]
    assert all(t.priority == "high" for t in design.test_cases if t.type == "boundary")


@pytest.mark.parametrize(
    "text,expected",
    [
        (
            "Passwords must be at least 8 characters long.",
            ["Boundary just below minimum: 7", "Boundary minimum: 8"],
        ),
        (
            "Users may upload up to 10 files.",
            ["Boundary maximum: 10", "Boundary just above maximum: 11"],
        ),
        (
            "The OTP is a 6-digit code.",
            [
                "Boundary 5 characters: length 5",
                "Boundary 6 characters: length 6",
                "Boundary 7 characters: length 7",
            ],
        ),
        (
            "Refunds of no more than 2.5 per day.",
            ["Boundary maximum: 2.50", "Boundary just above maximum: 2.60"],
        ),
    ],
)
def test_single_sided_and_length_limits(text, expected):
    found = titles(design_tests([req(text)]), "boundary")
    for title in expected:
        assert title in found


def test_timing_limit():
    design = design_tests([req("The host must respond within 30 seconds.")])
    assert "Timing at the 30 seconds limit" in titles(design, "boundary")


def test_negative_and_security_cases():
    design = design_tests([req("The switch must not log the PIN block.")])
    kinds = {t.type for t in design.test_cases}
    assert {"positive", "negative", "security"} <= kinds
    assert next(t for t in design.test_cases if t.type == "security").priority == "high"


def test_plain_requirement_gets_only_positive():
    design = design_tests([req("The dashboard shall show the company logo.")])
    assert [t.type for t in design.test_cases] == ["positive"]


@pytest.mark.parametrize(
    "text,kind,fragment",
    [
        ("The page should load fast.", "missing_acceptance_criteria", "measurable"),
        ("The UI must be user-friendly.", "ambiguous", "user-friendly"),
        ("Errors must flag mismatches and/or duplicates.", "ambiguous", "and/or"),
        ("The switch shall be available at all times.", "untestable", "Absolute"),
        ("The fee is TBD.", "incomplete", "TBD"),
        ("Users should get an email.", "ambiguous", "should"),
    ],
)
def test_gap_detection(text, kind, fragment):
    gaps = find_gaps([req(text)])
    assert any(g.kind == kind and fragment in g.issue for g in gaps), gaps


def test_fast_not_double_reported():
    gaps = find_gaps([req("Search must be fast.")])
    assert [g.kind for g in gaps] == ["missing_acceptance_criteria"]


def test_clear_requirements_have_no_gaps():
    gaps = find_gaps(
        [
            req("The switch must never log the full PAN."),
            req("Responses must arrive within 2 seconds at the 95th percentile."),
            req("Amounts must be between 1 and 100."),
        ]
    )
    assert gaps == []
