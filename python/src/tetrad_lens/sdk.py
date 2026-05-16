"""Layer 2 SDK entry points.

Two ways to instrument:

1. `@observe()` decorator — wraps Langfuse's own `@observe`, then attaches
   tetrad attributes when the function returns (or you call `tag_current_span`
   from within). Supports both sync and async functions; for async the wrapper
   returns an awaitable so callers `await observe(fn)(...)` cleanly.
2. `install_processor()` — installs PII masking on the active Langfuse v4
   client and propagates the tetrad attribute set into OTel baggage so child
   spans inherit it. Langfuse v4 owns the OTel SpanProcessor lifecycle from
   the `LANGFUSE_PUBLIC_KEY` / `LANGFUSE_SECRET_KEY` / `LANGFUSE_HOST` env
   vars; this function never calls `LangfuseSpanProcessor(...)` directly
   (its v4 constructor requires those credentials and we want this function
   to no-op gracefully without them).

PII masking is default ON.
"""

from __future__ import annotations

import asyncio
import functools
import logging
from collections.abc import Callable, Iterator
from contextlib import contextmanager, suppress
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


from opentelemetry import baggage, context, trace

from tetrad_lens.masking import mask_data
from tetrad_lens.schema import TetradSpan

F = TypeVar("F", bound=Callable[..., Any])

_INSTALLED = False
_BAGGAGE_PREFIX = "tetrad."


def install_processor(*, mask: bool = True, silence_langfuse_auth_warnings: bool = True) -> None:
    """Wire PII masking into the Langfuse v4 client (idempotent).

    Langfuse v4 stores the user-supplied masker on the client as ``_mask`` (set
    inside ``Langfuse(mask=...)``). The public attribute ``mask`` is NOT read by
    the upload path — assigning to it is a silent no-op. We therefore set
    ``client._mask`` directly. The private-attribute access is the only post-init
    path available; it is guarded so a different Langfuse version (where the
    attribute moves or vanishes) degrades gracefully rather than crashes.

    ``silence_langfuse_auth_warnings=True`` raises the Langfuse logger threshold
    to ERROR so quickstart users without credentials don't see scary "no
    public_key" warnings on stderr.
    """
    global _INSTALLED
    if _INSTALLED:
        return

    if not _HAVE_LANGFUSE:
        _INSTALLED = True
        return

    if silence_langfuse_auth_warnings:
        logging.getLogger("langfuse").setLevel(logging.ERROR)

    if mask:
        try:
            client = get_client()
        except Exception:
            client = None
        if client is not None:
            # v4 reads self._mask; setting self.mask is a no-op. We try both
            # so a future v5 that flips the public/private split keeps working.
            with suppress(Exception):
                client._mask = mask_data  # type: ignore[attr-defined, assignment]
            with suppress(Exception):
                client.mask = mask_data  # type: ignore[attr-defined, assignment]
            # Mirror the masker onto the inner resources object too — v4 stores
            # the masker on the shared resources singleton and the OTel
            # SpanProcessor reads it from there.
            resources = getattr(client, "_resources", None)
            if resources is not None:
                with suppress(Exception):
                    resources.mask = mask_data  # type: ignore[attr-defined]

    _INSTALLED = True


def _attach_baggage(span_data: TetradSpan) -> None:
    """Propagate tetrad attributes into OTel baggage so child spans inherit them."""
    ctx = context.get_current()
    for key, value in span_data.to_otel_attributes().items():
        if key.startswith(_BAGGAGE_PREFIX):
            ctx = baggage.set_baggage(key, str(value), context=ctx)
    context.attach(ctx)


def observe(
    *,
    name: str | None = None,
    capture_input: bool = True,
    capture_output: bool = True,
    mask: bool = True,
) -> Callable[[F], F]:
    """Drop-in replacement for ``langfuse.observe()`` that ensures PII masking
    is on and preserves sync/async signature parity.

    Usage::

        from tetrad_lens import observe, tag_current_span, TetradScore, TetradSpan

        @observe(name="generate-response")
        async def generate(prompt: str) -> str:
            ...
    """

    install_processor(mask=mask)

    def _decorate(fn: F) -> F:
        wrapped = _langfuse_observe(
            name=name,
            capture_input=capture_input,
            capture_output=capture_output,
        )(fn)

        # Langfuse v4 already preserves the original signature on `wrapped`
        # (sync wraps sync, async wraps async). Returning it directly avoids
        # an extra sync layer that would hide the inner coroutine from
        # frameworks that introspect with `asyncio.iscoroutinefunction`.
        if asyncio.iscoroutinefunction(fn):
            return wrapped  # type: ignore[return-value]

        # For sync functions we still keep an explicit wrapper so the
        # `functools.wraps` metadata stays bound to the user-visible callable.
        @functools.wraps(fn)
        def _runner(*args: Any, **kwargs: Any) -> Any:
            return wrapped(*args, **kwargs)

        return _runner  # type: ignore[return-value]

    return _decorate


def tag_current_span(span_data: TetradSpan, *, propagate_baggage: bool = True) -> None:
    """Attach tetrad attributes to the currently active OTel span.

    Call from inside a function decorated with ``@observe(...)`` or from anywhere
    inside a Langfuse trace context. When ``propagate_baggage`` is true the
    tetrad attributes are also pushed into OTel baggage so child spans inherit
    them (useful when a tagged parent span fans out to many leaves).
    """
    otel_span = trace.get_current_span()
    attrs = span_data.to_otel_attributes()
    if otel_span is not None and otel_span.is_recording():
        for key, value in attrs.items():
            otel_span.set_attribute(key, value)
    if propagate_baggage:
        _attach_baggage(span_data)


@contextmanager
def tetrad_context(name: str) -> Iterator[Any]:
    """Lightweight context manager for ad-hoc instrumentation.

    Yields the active OTel span so callers can attach tetrad attributes
    without using the decorator.
    """
    tracer = trace.get_tracer("tetrad-lens")
    with tracer.start_as_current_span(name) as span:
        yield span
