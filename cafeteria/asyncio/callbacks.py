from __future__ import annotations

from asyncio import Task, iscoroutinefunction, create_task, get_running_loop
from dataclasses import field, dataclass
from enum import Enum
from logging import getLogger
from typing import List, Any, Dict, NoReturn
from typing import Union, Generator, Callable, Coroutine, Tuple

from cafeteria.logging import LoggedObject

CallbackType = Union[Callable, Coroutine, "Callback"]
CallbackResultType = Union[Task, Generator]

logger = getLogger()


@dataclass
class Callback:
    function: CallbackType
    args: Tuple[Any] = field(default_factory=list)
    kwargs: Dict[str, Any] = field(default_factory=dict)

    def __init__(self, function, *args: Any, **kwargs: Any) -> None:
        super().__init__()
        self.function = function
        self.args = args
        self.kwargs = kwargs

    def trigger(self, *args: Any, **kwargs) -> CallbackResultType:
        """
        Trigger this callback by prepending given positional arguments and merging
        given keyword arguments updating default keyword arguments.

        :param args: Positional arguments to prepend.
        :param kwargs: Keyword arguments to update defaults with.
        :return: An awaitable result.
        """
        kwargz = dict(**self.kwargs)
        kwargz.update(kwargs)
        argz = args + self.args
        return trigger_callback(self.function, *argz, **kwargz)


@dataclass
class SimpleTriggerCallback(Callback):
    """
    A callback dataclass implementation that allows for ignoring any additional
    arguments provided at the time of trigger.
    """

    def __init__(self, function, *args: Any, **kwargs: Any) -> None:
        super().__init__(function, *args, **kwargs)

    def trigger(self, *_, **__) -> CallbackResultType:
        """
        Trigger callback ignoring provided arguments.
        """
        return super().trigger()


def trigger_callback(callback: CallbackType, *args, **kwargs) -> CallbackResultType:
    """
    Helper function to trigger a callback (coroutine or callable) with the provided
    positional/keyword arguments. This will return an awaitable callback result.

    :param callback: The callback to use for this trigger. This could be a `Coroutine`,
        `Callable` or a instance of `cafeteria.asyncio.callbacks.Callback`.
    :param args: The positional arguments to use when triggering a callback.
    :param kwargs: The keyword arguments to use when triggering a callback.
    :return: An awaitable result.
    """
    if isinstance(callback, Callback):
        return callback.trigger(*args, **kwargs)
    try:
        if iscoroutinefunction(callback):
            return create_task(callback(*args, **kwargs))
        else:
            return get_running_loop().run_in_executor(
                None, lambda: callback(*args, **kwargs)
            )
    except RuntimeError:
        logger.warning(
            "Callback triggered without a running loop, skipping %s", callback
        )


class CallbackRegistry(LoggedObject):
    def __init__(self) -> None:
        self._callbacks: Dict[Enum, List[Callback]] = dict()

    def register(self, event_type: Enum, callback: CallbackType) -> NoReturn:
        """
        This method allows for a handler to be registered for a specified event type.

        :param event_type: The type of event to associate the callback handler with.
        :param callback: The callback handler to associate with this event.
        """
        if not isinstance(callback, Callback):
            callback = Callback(function=callback)

        if event_type not in self._callbacks:
            self._callbacks[event_type] = list()
        self._callbacks[event_type].append(callback)
        self.logger.debug("Registered %s to %s", event_type.value, callback)

    async def handle_event(
        self, event_type: Enum, *args: Any, **kwargs: Any
    ) -> NoReturn:
        """
        Method called when an event is to be dispatched/handled. This arguments expects
        any additional positional/keyword arguments required when triggering the
        callback.

        :param event_type:
        :param args: Positional arguments to be passed into the callback before any
            pre-configured positional arguments.
        :param kwargs: Keyword arguments to be passed when triggering the callback.
            These override any pre-configured arguments.
        """
        self.logger.debug("Received event %s", event_type.value)
        if event_type in self._callbacks:
            for callback in self._callbacks[event_type]:
                self.logger.debug("Executing callback %s", callback)
                _ = callback.trigger(*args, **kwargs)
