"""Remove card data before text is shown, stored or sent to a model.

PANs keep the first 6 and last 4 digits (allowed for display under PCI DSS).
Track 2 discretionary data, PIN blocks and CVVs are removed entirely.
"""

import re
from dataclasses import dataclass

# 13 to 19 digits, optionally grouped by spaces or dashes, not part of a longer number
_PAN = re.compile(r"(?<![\d-])(?:\d[ -]?){12,18}\d(?![\d-])")
# PAN, separator (= or D), then expiry and discretionary data
_TRACK2 = re.compile(r"(?<!\d)(\d{13,19})([=D])(\d{4,})(\w*)")
_PIN_BLOCK = re.compile(r"(?i)\b(pin[ _-]?block|field[ _]?52|f52|de52)(\s*[:=]\s*)([0-9a-f]{16})\b")
_CVV = re.compile(r"(?i)\b(cvv2?|cvc2?|cid)(\s*[:=]\s*)(\d{3,4})\b")


def luhn_valid(digits: str) -> bool:
    total = 0
    for i, ch in enumerate(reversed(digits)):
        d = int(ch)
        if i % 2:
            d = d * 2 - 9 if d > 4 else d * 2
        total += d
    return total % 10 == 0


def mask_pan(pan: str) -> str:
    return pan[:6] + "*" * (len(pan) - 10) + pan[-4:]


@dataclass
class MaskResult:
    text: str
    pans: int = 0
    track2: int = 0
    pin_blocks: int = 0
    cvvs: int = 0

    @property
    def total(self) -> int:
        return self.pans + self.track2 + self.pin_blocks + self.cvvs


def mask(text: str) -> MaskResult:
    result = MaskResult(text)

    def track2(m: re.Match) -> str:
        result.track2 += 1
        return mask_pan(m.group(1)) + m.group(2) + "*" * len(m.group(3) + m.group(4))

    def pin(m: re.Match) -> str:
        result.pin_blocks += 1
        return m.group(1) + m.group(2) + "*" * 16

    def cvv(m: re.Match) -> str:
        result.cvvs += 1
        return m.group(1) + m.group(2) + "***"

    def pan(m: re.Match) -> str:
        digits = re.sub(r"\D", "", m.group(0))
        # Only Luhn-valid numbers are card numbers; STANs, RRNs and amounts are left alone.
        if not luhn_valid(digits):
            return m.group(0)
        result.pans += 1
        return mask_pan(digits)

    text = _TRACK2.sub(track2, text)
    text = _PIN_BLOCK.sub(pin, text)
    text = _CVV.sub(cvv, text)
    result.text = _PAN.sub(pan, text)
    return result


def contains_card_data(text: str) -> bool:
    return mask(text).total > 0
