"""@observe preserves async callable identity (audit fix from M-B)."""

from __future__ import annotations

import asyncio

import pytest

from tetrad_lens import observe


@pytest.mark.asyncio
async def test_observe_preserves_async_signature():
    @observe(name="async-step")
    async def add(a: int, b: int) -> int:
        await asyncio.sleep(0)
        return a + b

    assert asyncio.iscoroutinefunction(add), (
        "@observe must keep an async function async; framework introspection "
        "(FastAPI, anyio, OTel async context) breaks otherwise."
    )
    result = await add(2, 3)
    assert result == 5


@pytest.mark.asyncio
async def test_observe_sync_still_works():
    @observe(name="sync-step")
    def square(x: int) -> int:
        return x * x

    assert square(4) == 16
    assert not asyncio.iscoroutinefunction(square)
