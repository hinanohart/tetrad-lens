"""Tier 3: human-review queue.

Thin wrapper around the Langfuse Score API. The contract:

- Tier 3 scores are written with `metadata={"tetrad_lens.source": "ANNOTATION"}`
  and a `comment` prefix of `[ANNOTATION:<annotator>]`. The Langfuse v4 score
  API no longer accepts a `source=` kwarg directly; the server-side ScoreSource
  field tracks "where the API call came from", which is what we want.
- Tier 3 scores always overwrite the active tetrad attributes on the span
- We do not provide a UI; we lean on Langfuse's standard chart + Score filter
  to surface low-confidence spans first (see docs/case_study_*.md).

If `langfuse` is not installed, *or* the runtime client cannot be obtained
(no credentials in env), we keep an in-memory queue so tests and offline use
both work.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from tetrad_lens.schema import TetradSpan

try:
    from langfuse import get_client  # type: ignore[import-not-found]

    _HAVE_LANGFUSE = True
except Exception:
    _HAVE_LANGFUSE = False

    def get_client() -> Any:  # type: ignore[misc]
        return None


@dataclass
class ReviewQueueClient:
    """Posts annotation scores back to Langfuse using its score API."""

    config_name: str = "tetrad_v1"
    in_memory: list[dict[str, Any]] = field(default_factory=list)

    def submit(
        self,
        *,
        trace_id: str,
        observation_id: str | None = None,
        span_data: TetradSpan,
        annotator: str = "human",
        comment: str | None = None,
    ) -> None:
        """Write four scores (one per axis) under the tetrad_v1.* config namespace."""
        if span_data.tier != "annotation":
            raise ValueError(
                "ReviewQueueClient only accepts span_data.tier == 'annotation' "
                "(human-review queue overrides everything else)"
            )

        payloads = [
            {
                "name": f"{self.config_name}.enhance",
                "value": span_data.enhance.score,
                "comment": span_data.enhance.rationale,
            },
            {
                "name": f"{self.config_name}.obsolesce",
                "value": span_data.obsolesce.score,
                "comment": span_data.obsolesce.rationale,
            },
            {
                "name": f"{self.config_name}.retrieve",
                "value": span_data.retrieve.score,
                "comment": span_data.retrieve.rationale,
            },
            {
                "name": f"{self.config_name}.reverse",
                "value": span_data.reverse.score,
                "comment": span_data.reverse.rationale,
            },
        ]

        client = None
        if _HAVE_LANGFUSE:
            try:
                candidate = get_client()
            except Exception:
                candidate = None
            # Langfuse v4 returns a *disabled* client (public_key=None) when no
            # credentials are configured. Treat that as offline.
            if candidate is not None and getattr(candidate, "public_key", None):
                client = candidate

        if client is None:
            # Offline / no credentials / langfuse missing — keep in-memory.
            for p in payloads:
                self.in_memory.append(
                    {
                        **p,
                        "trace_id": trace_id,
                        "observation_id": observation_id,
                        "annotator": annotator,
                    }
                )
            return

        annotation_prefix = f"[ANNOTATION:{annotator}]"
        for p in payloads:
            kwargs: dict[str, Any] = {
                "trace_id": trace_id,
                "name": p["name"],
                "value": p["value"],
                "data_type": "NUMERIC",
                "metadata": {
                    "tetrad_lens.source": "ANNOTATION",
                    "tetrad_lens.annotator": annotator,
                },
            }
            if observation_id is not None:
                kwargs["observation_id"] = observation_id

            parts: list[str] = [annotation_prefix]
            axis_comment = p["comment"]
            if isinstance(axis_comment, str) and axis_comment:
                parts.append(axis_comment)
            if comment:
                parts.append(comment)
            kwargs["comment"] = " ".join(parts)

            create = getattr(client, "create_score", None)
            if create is not None:
                create(**kwargs)
