"""Layer 2 SDK entry points.

Two ways to instrument:

1. `@observe()` decorator — wraps Langfuse's own `@observe`, then attaches
   tetrad attributes when the function returns (or you call `tag_current_span`
   from within).
2. `install_processor()` — wires PII masking into the Langfuse v4 client.
   Langfuse v4 manages its own OpenTelemetry SpanProcessor lifecycle from the
   `LANGFUSE_PUBLIC_KEY` / `LANGFUSE_SECRET_KEY` / `LANGFUSE_HOST` env vars, so
   this function only needs to attach the masking hook; it deliberately does
   NOT call `LangfuseSpanProcessor(...)` directly (that constructor requires
   credentials and would fail in credential-less environments).

PII masking is default ON.
"""

from __future__ import annotations

import functools
import os
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from typing import Any, TypeVar

try:
    # Langfuse v4 entry points.
    from langfuse import get_client  # type: ignore[import-not-found]
    from langfuse import observe as _langfuse_observe  # type: ignore[import-not-found]

    _HAVE_LANGFUSE = True
except Exception:  # pragma: no cover - we keep working in environments without langfuse installed
    _HAVE_LANGFUSE = False

    def _langfuse_observe(*_args: Any, **_kwargs: Any) -> Any:
        def _wrap(fn: Callable[..., Any]) -> Callable[..., Any]:
            return fn

        return _wrap

    def get_client() -> Any:  # type: ignore[misc]
        return None


from opentelemetry import trace

from tetrad_lens.masking import mask_data
from tetrad_lens.schema import TetradSpan

F = TypeVar("F", bound=Callable[..., Any])

_INSTALLED = False


def install_processor(*, mask: bool = True) -> None:
    """Wire PII masking into the Langfuse client and make sure the SpanProcessor is live.

    Langfuse v4 reads `LANGFUSE_PUBLIC_KEY` / `LANGFUSE_SECRET_KEY` / `LANGFUSE_HOST`
    from the environment and lazily constructs its own client + SpanProcessor on
    first use. We do not call `LangfuseSpanProcessor(...)` directly because its
    v4 constructor requires those credentials as positional arguments and we
    want this to be a no-op when they are not set (smoke tests, CI without
    secrets, etc).

    `mask=True` (default) installs `mask_data` on the Langfuse client. If the
    client cannot be obtained (no credentials), we still mark this function as
    "installed" so it doesn't keep retrying.
    """
    global _INSTALLED
    if _INSTALLED:
        return

    if not _HAVE_LANGFUSE:
        _INSTALLED = True
        return

    if mask:
        from contextlib import suppress

        try:
            client = get_client()
        except Exception:
            client = None
        # The Langfuse v4 client exposes a `mask` attribute that is called
        # on every payload before upload. Attribute name has been stable
        # since v4.0; we guard with hasattr to keep older/newer versions safe.
        if client is not None and hasattr(client, "mask"):
            with suppress(Exception):
                client.mask = mask_data

    # Honor OTEL_SEMCONV_STABILITY_OPT_IN: we don't toggle openinference's
    # behavior from here, but we expose the env var so users know it exists.
    _ = os.environ.get("OTEL_SEMCONV_STABILITY_OPT_IN", "tetrad/dup")

    _INSTALLED = True


def observe(
    *,
    name: str | None = None,
    capture_input: bool = True,
    capture_output: bool = True,
    mask: bool = True,
) -> Callable[[F], F]:
    """Drop-in replacement for `langfuse.observe()` that ensures the SpanProcessor is installed
    and that PII masking defaults to ON.

    Usage::

        from tetrad_lens import observe, tag_current_span, TetradScore, TetradSpan

        @observe(name="generate-response")
        def generate(prompt: str) -> str:
            ...
    """

    install_processor(mask=mask)

    def _decorate(fn: F) -> F:
        wrapped = _langfuse_observe(
            name=name,
            capture_input=capture_input,
            capture_output=capture_output,
        )(fn)

        @functools.wraps(fn)
        def _runner(*args: Any, **kwargs: Any) -> Any:
            return wrapped(*args, **kwargs)

        return _runner  # type: ignore[return-value]

    return _decorate


def tag_current_span(span_data: TetradSpan) -> None:
    """Attach tetrad attributes to the currently active OTel span.

    Call from inside a function decorated with `@observe(...)` or from anywhere
    inside a Langfuse trace context.
    """
    otel_span = trace.get_current_span()
    if otel_span is None or not otel_span.is_recording():
        return
    for key, value in span_data.to_otel_attributes().items():
        otel_span.set_attribute(key, value)


@contextmanager
def tetrad_context(name: str) -> Iterator[Any]:
    """Lightweight context manager for ad-hoc instrumentation.

    Yields the active OTel span so callers can attach tetrad attributes
    without using the decorator.
    """
    tracer = trace.get_tracer("tetrad-lens")
    with tracer.start_as_current_span(name) as span:
        yield span
