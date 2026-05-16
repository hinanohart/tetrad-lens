"""Quickstart: tag a snippet, print the OTel attributes.

Run from the repo root:

    cd python && pip install -e ".[dev]"
    python ../examples/quickstart.py
"""

from __future__ import annotations

import json

from tetrad_lens import observe
from tetrad_lens.heuristic import tag_heuristically
from tetrad_lens.sdk import tag_current_span


SAMPLE = (
    "Replace the nightly poll job with the new event bus. "
    "Old call sites will receive a callback instead. "
    "This should accelerate billing reconciliation."
)


@observe(name="quickstart-example")
def score_and_attach(text: str) -> dict[str, float | str]:
    span_data = tag_heuristically(text)
    tag_current_span(span_data)
    return span_data.to_otel_attributes()


if __name__ == "__main__":
    print(json.dumps(score_and_attach(SAMPLE), indent=2, ensure_ascii=False))
