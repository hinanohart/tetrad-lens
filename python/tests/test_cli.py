"""CLI smoke tests."""

from __future__ import annotations

import json

from tetrad_lens.cli import main


def test_version(capsys):
    rc = main(["--version"])
    out = capsys.readouterr().out
    assert rc == 0
    assert "tetrad-lens" in out
    assert "schema" in out


def test_tag_smoke(capsys):
    rc = main(["tag", "--text", "accelerate code review and optimize throughput"])
    out = capsys.readouterr().out
    payload = json.loads(out)
    assert rc == 0
    assert "tetrad.enhance" in payload
    assert "tetrad.schema_version" in payload
