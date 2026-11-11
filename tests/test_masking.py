import pytest

from ayewo.masking import contains_card_data, luhn_valid, mask, mask_pan


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("pan=4111111111111111 ok", "pan=411111******1111 ok"),
        ("card 4111 1111 1111 1111 used", "card 411111******1111 used"),
        ("card 5555-5555-5555-4444.", "card 555555******4444."),
        ("19 digit 5061000000000000007", "19 digit 506100*********0007"),
    ],
)
def test_pans_masked(raw, expected):
    assert mask(raw).text == expected


@pytest.mark.parametrize(
    "safe",
    [
        "stan=000123 rrn=631509000123",
        "amount=5000000 at 2026-11-11 09:30:00.120",
        "ref 1234567890123456",  # 16 digits but not Luhn valid
        "id 4111111111111111111111",  # too long to be a PAN
    ],
)
def test_non_card_numbers_untouched(safe):
    result = mask(safe)
    assert result.text == safe
    assert result.total == 0


def test_track2_both_separators():
    assert mask("t2=4111111111111111=2812201123").text == "t2=411111******1111=**********"
    result = mask("track2=5555555555554444D2812201")
    assert result.text == "track2=555555******4444D*******"
    assert result.track2 == 1 and result.pans == 0


def test_pin_block_and_cvv():
    result = mask("PIN block: 0A1B2C3D4E5F6071 field52=FFFFFFFFFFFFFFFF cvv2=123 CVC: 9876")
    assert "0A1B2C3D4E5F6071" not in result.text
    assert "field52=****************" in result.text
    assert "cvv2=***" in result.text and "CVC: ***" in result.text
    assert result.pin_blocks == 2 and result.cvvs == 2


def test_helpers():
    assert luhn_valid("4111111111111111")
    assert not luhn_valid("4111111111111112")
    assert mask_pan("5555555555554444") == "555555******4444"
    assert contains_card_data("x 4111111111111111")
    assert not contains_card_data("stan=000123")
