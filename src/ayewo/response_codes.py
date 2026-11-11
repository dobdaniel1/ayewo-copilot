RESPONSE_CODES = {
    "00": "Approved",
    "05": "Do not honour",
    "12": "Invalid transaction",
    "13": "Invalid amount",
    "14": "Invalid card number",
    "30": "Format error",
    "41": "Lost card",
    "43": "Stolen card",
    "51": "Insufficient funds",
    "54": "Expired card",
    "55": "Incorrect PIN",
    "57": "Transaction not permitted to cardholder",
    "61": "Exceeds withdrawal amount limit",
    "65": "Exceeds withdrawal frequency limit",
    "68": "Response received too late",
    "75": "PIN tries exceeded",
    "91": "Issuer or switch inoperative",
    "92": "No route to issuer",
    "94": "Duplicate transmission",
    "96": "System malfunction",
}

ISSUER_DECLINES = {"05", "12", "13", "14", "41", "43", "51", "54", "55", "57", "61", "65", "75"}
SYSTEM_FAILURES = {"68", "91", "92", "96"}


def meaning(code: str) -> str:
    return RESPONSE_CODES.get(code, "Unknown response code")
