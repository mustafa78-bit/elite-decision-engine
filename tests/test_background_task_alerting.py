"""Tests for api.main._on_task_done -- the done-callback attached to every
background task started in lifespan() so an unhandled exception in a task
that runs forever gets a real logged alert instead of silently vanishing.
"""

import asyncio
import logging

import pytest

from api.main import _on_task_done


async def _completes_normally():
    return "ok"


async def _raises():
    raise ValueError("kaboom")


async def _runs_forever():
    await asyncio.sleep(10)


async def test_normal_completion_does_not_alert(caplog):
    caplog.set_level(logging.CRITICAL)
    task = asyncio.create_task(_completes_normally())
    task.add_done_callback(_on_task_done("normal task"))

    await task
    await asyncio.sleep(0)

    assert "died unexpectedly" not in caplog.text


async def test_exception_triggers_critical_alert_with_task_name(caplog):
    caplog.set_level(logging.CRITICAL)
    task = asyncio.create_task(_raises())
    task.add_done_callback(_on_task_done("boom task"))

    with pytest.raises(ValueError):
        await task
    await asyncio.sleep(0)

    critical_records = [r for r in caplog.records if r.levelno == logging.CRITICAL]
    assert len(critical_records) == 1
    assert "boom task" in critical_records[0].getMessage()
    assert "died unexpectedly" in critical_records[0].getMessage()


async def test_cancelled_task_does_not_alert(caplog):
    caplog.set_level(logging.CRITICAL)
    task = asyncio.create_task(_runs_forever())
    task.add_done_callback(_on_task_done("cancelled task"))

    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task
    await asyncio.sleep(0)

    assert "died unexpectedly" not in caplog.text
