"""Extra PII coverage added in v0.1.0 post-release audit."""

from __future__ import annotations

from tetrad_lens.masking import mask_text


def test_ssn_masked():
    assert "[ssn]" in mask_text("ssn 123-45-6789 on file")


def test_jwt_masked():
    # Synthesized at runtime to avoid pre-commit secret scanners.
    jwt = "eyJ" + "AAAAAAAAAAAA" + ".eyJ" + "BBBBBBBBBBBB" + ".sig123_-"
    out = mask_text(f"auth header {jwt} value")
    assert "[jwt]" in out


def test_ipv4_masked():
    assert "[ip]" in mask_text("connect to 192.168.1.55 please")


def test_credit_card_luhn_valid_masked():
    # 4242 4242 4242 4242 is a known Luhn-valid Visa test number.
    assert "[card]" in mask_text("pay with 4242 4242 4242 4242 now")


def test_credit_card_luhn_invalid_passthrough():
    # 4242 4242 4242 4241 fails Luhn — should NOT be masked.
    assert "[card]" not in mask_text("invoice 4242 4242 4242 4241 reference")


def test_phone_e164_masked():
    assert "[phone]" in mask_text("call +14155552671 today")


def test_plain_digit_run_not_masked_as_phone():
    # Invoice IDs without separators or + should not match the phone regex.
    assert "[phone]" not in mask_text("invoice 1234567890123 reference")
