import asyncio
from asyncio import Task
from typing import Any, Coroutine, Union


def execute_async_method(coroutine: Coroutine) -> Union[Any, Task]:
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()

    if loop.is_running():
        return loop.create_task(coroutine)
    else:
        return loop.run_until_complete(coroutine)
