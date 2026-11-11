"""Pull individual requirements out of an SRS, PRD or user story file."""

import re

from .models import Requirement

# "REQ-001: text", "- **FR-12** text", "NFR 3. text"
_WITH_ID = re.compile(
    r"^\s*(?:[-*+]\s+|\d+[.)]\s+)?\**\s*((?:REQ|FR|NFR|BR|SR|US|AC)[-_ ]?\d+[A-Za-z]?)\s*\**\s*[:.)-]?\s*(.+)$",
    re.IGNORECASE,
)
# Bullet or numbered items that state an obligation
_LIST_ITEM = re.compile(r"^\s*(?:[-*+]|\d+[.)])\s+(.+)$")
_OBLIGATION = re.compile(r"\b(shall|must|should|will|is required to|needs? to)\b", re.IGNORECASE)


def parse_requirements(text: str) -> list[Requirement]:
    requirements: list[Requirement] = []
    seen: set[str] = set()
    auto = 0
    for line_no, line in enumerate(text.splitlines(), start=1):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if m := _WITH_ID.match(line):
            req_id = re.sub(r"[_ ]", "-", m.group(1).upper())
            body = m.group(2).strip()
        elif (m := _LIST_ITEM.match(line)) and _OBLIGATION.search(m.group(1)):
            auto += 1
            req_id = f"REQ-{auto:03d}"
            while req_id in seen:
                auto += 1
                req_id = f"REQ-{auto:03d}"
            body = m.group(1).strip()
        else:
            continue
        body = body.strip("* ")
        if req_id in seen or not body:
            continue
        seen.add(req_id)
        requirements.append(Requirement(id=req_id, text=body, line=line_no))
    return requirements
