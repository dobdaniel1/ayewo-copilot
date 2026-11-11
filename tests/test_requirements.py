from ayewo.requirements import parse_requirements


def test_explicit_ids_and_formats():
    text = """# Heading REQ-999: ignored because it is a heading
- REQ-001: First requirement.
- **FR-12** Second requirement
NFR_3. Third requirement
1. us 4) Fourth requirement
"""
    reqs = parse_requirements(text)
    assert [(r.id, r.text) for r in reqs] == [
        ("REQ-001", "First requirement."),
        ("FR-12", "Second requirement"),
        ("NFR-3", "Third requirement"),
        ("US-4", "Fourth requirement"),
    ]
    assert reqs[0].line == 2


def test_auto_ids_for_obligation_bullets():
    text = """Intro paragraph that shall be ignored because it is not a list item.
- The system shall log every login.
- A nice to have feature
* Users must reset passwords every 90 days.
2. The API will return JSON.
"""
    reqs = parse_requirements(text)
    assert [r.id for r in reqs] == ["REQ-001", "REQ-002", "REQ-003"]
    assert reqs[1].text.startswith("Users must reset")


def test_auto_ids_skip_existing_and_duplicates():
    text = (
        "- REQ-001: Explicit one.\n- The system shall do more.\n- REQ-001: Duplicate id ignored.\n"
    )
    assert [r.id for r in parse_requirements(text)] == ["REQ-001", "REQ-002"]


def test_example_spec(spec_path):
    reqs = parse_requirements(spec_path.read_text())
    assert len(reqs) == 14
    assert reqs[-1].id == "REQ-014"
