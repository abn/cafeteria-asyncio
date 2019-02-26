import asyncio
import signal
from asyncio import AbstractEventLoop


async def cancel_all_tasks(event_loop: AbstractEventLoop = None):
    event_loop = event_loop or asyncio.get_running_loop()
    for task in asyncio.Task.all_tasks(event_loop):
        if task is asyncio.Task.current_task():
            continue
        if not task.done():
            task.cancel()
            await task
    event_loop.stop()


def handle_signals(event_loop, *signames):
    for sig in {"SIGINT", "SIGTERM", *signames}:
        event_loop.add_signal_handler(
            getattr(signal, sig), lambda: asyncio.ensure_future(cancel_all_tasks())
        )
