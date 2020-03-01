import asyncio
import signal

import pytest

from cafeteria.asyncio.commons import cancel_all_tasks, cancel_tasks_on_termination


# noinspection PyUnresolvedReferences,PyProtectedMember
def ensure_signal_handlers_registered(
    loop: asyncio.AbstractEventLoop, *args: signal.Signals
) -> None:
    assert len(loop._signal_handlers) == 2 + len(args)

    # ensure default signal handlers registered added
    assert signal.SIGINT in loop._signal_handlers
    assert signal.SIGTERM in loop._signal_handlers

    for arg in args:
        assert arg in loop._signal_handlers


def test_handle_signals(recwarn):
    # noinspection PyDeprecation
    from cafeteria.asyncio.commons import handle_signals

    loop = asyncio.get_event_loop()
    handle_signals(event_loop=loop)
    ensure_signal_handlers_registered(loop)

    # ensure a deprecation warning was issued
    assert len(recwarn) == 1
    w = recwarn.pop(DeprecationWarning)
    assert issubclass(w.category, DeprecationWarning)
    assert str(w.message) == "Use cancel_tasks_on_termination instead"


def test_cancel_tasks_on_termination_default():
    loop = asyncio.get_event_loop()
    cancel_tasks_on_termination(loop, signal.SIGABRT)
    ensure_signal_handlers_registered(loop, signal.SIGABRT)


def test_cancel_tasks_on_termination_int():
    loop = asyncio.get_event_loop()
    cancel_tasks_on_termination(loop, 6)
    ensure_signal_handlers_registered(loop, signal.SIGABRT)


def test_cancel_tasks_on_termination_str():
    loop = asyncio.get_event_loop()
    cancel_tasks_on_termination(loop, "SIGABRT")
    ensure_signal_handlers_registered(loop, signal.SIGABRT)


def test_cancel_tasks_on_termination_invalid_type(mocker):
    with pytest.raises(ValueError):
        # noinspection PyTypeChecker
        cancel_tasks_on_termination(asyncio.get_event_loop(), mocker.Mock())


def test_cancel_tasks_on_termination_invalid_int():
    with pytest.raises(ValueError):
        # noinspection PyTypeChecker
        cancel_tasks_on_termination(asyncio.get_event_loop(), 9999)


def test_cancel_tasks_on_termination_invalid_str():
    with pytest.raises(ValueError):
        # noinspection PyTypeChecker
        cancel_tasks_on_termination(asyncio.get_event_loop(), "FOOBAR")


@pytest.mark.asyncio
async def test_cancel_all_tasks():
    async def infinity():
        try:
            while True:
                await asyncio.sleep(2)
        except asyncio.CancelledError:
            pass

    test_task = asyncio.current_task()
    task = asyncio.ensure_future(infinity())

    # ensure task is running
    assert not (task.done() or task.cancelled())

    await cancel_all_tasks(None, test_task)
    assert task.cancelled()

    # current task was ignored
    assert not (test_task.done() or test_task.cancelled())
