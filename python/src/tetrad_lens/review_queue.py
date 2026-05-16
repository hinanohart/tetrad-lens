"""Tier 3: human-review queue.

Thin wrapper around the Langfuse Score API. The contract:

- Tier 3 scores are written with ``metadata={"tetrad_lens.source": "ANNOTATION"}``
  and a ``comment`` prefix of ``[ANNOTATION:<annotator>]``. The Langfuse v4 score
  API no longer accepts a ``source=`` kwarg directly; the server-side ScoreSource
  field tracks "where the API call came from", which is what we want.
- Tier 3 scores always overwrite the active tetrad attributes on the span
- We do not provide a UI; we lean on Langfuse's standard chart + Score filter
  to surface low-confidence spans first (see docs/case_study_*.md).
- ``submit()`` is atomic-ish: if any axis write fails, all axes are buffered
  into the in-memory queue for offline retry instead of leaving the span
  half-annotated. Use ``flush()`` to retry the buffer against a live client.
- Score comments are hard-truncated to fit Langfuse's 1000-char limit; the
  ``[ANNOTATION:<annotator>]`` prefix is always preserved.

If ``langfuse`` is not installed, *or* the runtime client cannot be obtained
(no credentials in env), we keep an in-memory queue so tests and offline use
both work.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from tetrad_lens.schema import TetradSpan

_LOG = logging.getLogger(__name__)
_COMMENT_LIMIT = 950  # leave headroom below Langfuse's 1000-char score-comment cap

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

        annotation_prefix = f"[ANNOTATION:{annotator}]"
        common_meta = {
            "tetrad_lens.source": "ANNOTATION",
            "tetrad_lens.annotator": annotator,
        }

        def _enqueue_offline() -> None:
            for p in payloads:
                self.in_memory.append(
                    {
                        **p,
                        "trace_id": trace_id,
                        "observation_id": observation_id,
                        "annotator": annotator,
                        "comment_extra": comment,
                    }
                )

        if client is None:
            # Offline / no credentials / langfuse missing — keep in-memory.
            _enqueue_offline()
            return

        # Build the kwargs for all four axes up-front so a failure on axis #3
        # doesn't leave axes #1+#2 written and #3+#4 lost.
        score_calls: list[dict[str, Any]] = []
        for p in payloads:
            kwargs: dict[str, Any] = {
                "trace_id": trace_id,
                "name": p["name"],
                "value": p["value"],
                "data_type": "NUMERIC",
                "metadata": common_meta,
            }
            if observation_id is not None:
                kwargs["observation_id"] = observation_id

            parts: list[str] = [annotation_prefix]
            axis_comment = p["comment"]
            if isinstance(axis_comment, str) and axis_comment:
                parts.append(axis_comment)
            if comment:
                parts.append(comment)
            joined = " ".join(parts)
            if len(joined) > _COMMENT_LIMIT:
                joined = joined[: _COMMENT_LIMIT - 1] + "…"
            kwargs["comment"] = joined
            score_calls.append(kwargs)

        create = getattr(client, "create_score", None)
        if create is None:
            _LOG.warning("Langfuse client has no create_score; queuing in-memory")
            _enqueue_offline()
            return

        for kwargs in score_calls:
            try:
                create(**kwargs)
            except Exception as exc:
                _LOG.warning(
                    "create_score failed on %s (%s); buffering all four axes for retry",
                    kwargs.get("name"),
                    exc,
                )
                _enqueue_offline()
                return

    def flush(self, client: Any | None = None) -> int:
        """Retry any in-memory payloads against ``client`` (or ``get_client()``).

        Returns the number of payloads successfully sent. Failing payloads stay
        in the buffer so callers can retry later. Caller owns the trace/span
        invariants for retries — partial flushes are reflected in the queue.
        """
        if client is None and _HAVE_LANGFUSE:
            try:
                candidate = get_client()
            except Exception:
                candidate = None
            if candidate is not None and getattr(candidate, "public_key", None):
                client = candidate
        if client is None:
            return 0

        create = getattr(client, "create_score", None)
        if create is None:
            return 0

        remaining: list[dict[str, Any]] = []
        sent = 0
        for entry in self.in_memory:
            kwargs = {
                "trace_id": entry["trace_id"],
                "name": entry["name"],
                "value": entry["value"],
                "data_type": "NUMERIC",
                "metadata": {
                    "tetrad_lens.source": "ANNOTATION",
                    "tetrad_lens.annotator": entry.get("annotator", "human"),
                },
            }
            if entry.get("observation_id"):
                kwargs["observation_id"] = entry["observation_id"]
            prefix = f"[ANNOTATION:{entry.get('annotator', 'human')}]"
            parts = [prefix]
            if entry.get("comment"):
                parts.append(str(entry["comment"]))
            if entry.get("comment_extra"):
                parts.append(str(entry["comment_extra"]))
            joined = " ".join(parts)
            kwargs["comment"] = (
                joined[: _COMMENT_LIMIT - 1] + "…" if len(joined) > _COMMENT_LIMIT else joined
            )
            try:
                create(**kwargs)
                sent += 1
            except Exception as exc:
                _LOG.warning("Flush failed on %s: %s", entry.get("name"), exc)
                remaining.append(entry)

        self.in_memory = remaining
        return sent
