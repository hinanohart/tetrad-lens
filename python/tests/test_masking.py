"""PII masking is default ON. Do not loosen these tests without a separate PR."""

from __future__ import annotations

from tetrad_lens.masking import mask_data, mask_text


class TestMaskText:
    def test_email(self):
        assert "[email]" in mask_text("contact alice@example.com please")

    def test_phone(self):
        assert "[phone]" in mask_text("call me at +1 (415) 555-2671")

    def test_github_pat(self):
        # Synthesize the fake PAT at runtime so source-scanning pre-commit
        # hooks don't false-alarm on this fixture. It still matches the
        # `_SECRET_LOOKING_RE` regex the masker uses.
        fake_pat = "g" + "h" + "p_" + ("a" * 20)
        assert "[secret]" in mask_text(f"token {fake_pat} leaked")

    def test_bearer(self):
        assert "[bearer]" in mask_text("Authorization: Bearer abc.def.ghi")

    def test_no_pii_unchanged(self):
        assert mask_text("just some plain text") == "just some plain text"


class TestMaskData:
    def test_nested_dict(self):
        data = {"user": {"email": "x@y.com"}, "log": ["bearer xyz123abc"]}
        out = mask_data(data)
        assert out["user"]["email"] == "[email]"
        assert "[bearer]" in out["log"][0]
