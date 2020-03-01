from __future__ import annotations

import asyncio
import logging
import warnings
from dataclasses import dataclass, field
from enum import Enum
from typing import (
    Any,
    Callable,
    Coroutine,
    Dict,
    Generator,
    Hashable,
    List,
    Optional,
    Tuple,
    Union,
)

from cafeteria.logging import LoggedObject

CallbackType = Union[Callable, Coroutine, "Callback"]
CallbackResultType = Union[asyncio.Task, Generator, Coroutine]
EventType = Optional[Union[Enum, Hashable, None]]

logger = logging.getLogger()


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
        `Callable` or a instance of :class:`cafeteria.asyncio.callbacks.Callback`.
    :param args: The positional arguments to use when triggering a callback.
    :param kwargs: The keyword arguments to use when triggering a callback.
    :return: An awaitable result.
    """
    if isinstance(callback, Callback):
        return callback.trigger(*args, **kwargs)

    if asyncio.iscoroutinefunction(callback):
        try:
            return asyncio.create_task(callback(*args, **kwargs))
        except RuntimeError:
            logger.warning(
                "Callback triggered without a running loop, skipping %s", callback
            )
    else:
        try:
            return asyncio.get_running_loop().run_in_executor(
                None, lambda: callback(*args, **kwargs)
            )
        except RuntimeError:
            callback(*args, **kwargs)


class CallbackRegistry(LoggedObject):
    def __init__(
        self, callbacks: Optional[Dict[EventType, CallbackType]] = None
    ) -> None:
        self._callbacks: Dict[EventType, List[Callback]] = dict()
        if callbacks is not None:
            for event_type, callback in callbacks.items():
                self.register(event_type, callback)

    def callbacks(self, event_type: EventType = None) -> List[Callback]:
        """
        Retrieve all callbacks registered for a particular *event_type*. If *event_type*
        is `None` or does not have any callbacks already registered, the default
        callbacks are returned.

        :param event_type: Event type to retrieve callbacks for.
        :return: Registered callbacks or default callbacks if none registered for the
            event type.
        """
        return self._callbacks.get(event_type, self._callbacks.get(None, []))

    def register(self, event_type: EventType, callback: CallbackType) -> None:
        """
        This method allows for a handler to be registered for a specified event type. If
        the *event_type* is `None` this is registered as a default callback triggered
        only when explicitly dispatched or no other event type matched the specified
        event type when dispatching.

        :param event_type: The type of event to associate the callback handler with.
        :param callback: The callback handler to associate with this event.
        """
        if not isinstance(callback, Callback):
            callback = Callback(function=callback)

        if event_type not in self._callbacks:
            self._callbacks[event_type] = list()
        self._callbacks[event_type].append(callback)
        self.logger.debug("Registered %s to %s", event_type, callback)

    def deregister(self, event_type: EventType, callback: CallbackType) -> None:
        """
        This method allows for a handler to be de-registered for a specified event type
        if it has already been registered. If *event_type* is set to `None`, *callback*
        is removed (if exists) from the default callbacks.

        :param event_type: The type of event the callback handler is associated with.
        :param callback: The callback handler to de-register.
        """
        if not isinstance(callback, Callback):
            callback = Callback(function=callback)

        try:
            self._callbacks.get(event_type, []).remove(callback)
        except ValueError:
            pass

    def exists(self, event_type: EventType, callback: CallbackType) -> bool:
        """
        Check if callback exists for the specified *event_type*

        :param event_type: The type of event to check the callback for.
        :param callback: The callback handler to de-register.
        :return: `True` if *callback* exists for the specified *event_type*.
        """
        if not isinstance(callback, Callback):
            callback = Callback(function=callback)
        return callback in self.callbacks(event_type)

    def dispatch(self, event_type: EventType, *args: Any, **kwargs: Any):
        """
        Dispatch callbacks registered for an *event_type*. This arguments expects
        any additional positional/keyword arguments required when triggering the
        callback. If *event_type* is `None` or does not have any callbacks already
         registered, the default callbacks (if any) are triggered.

        :param event_type: Event type to dispatch
        :param args: Positional arguments to be passed into the callback before any
            pre-configured positional arguments.
        :param kwargs: Keyword arguments to be passed when triggering the callback.
            These override any pre-configured arguments.
        """
        self.logger.debug("Received event: %s", event_type)
        for callback in self.callbacks(event_type):
            self.logger.debug("Executing callback %s", callback)
            _ = callback.trigger(*args, **kwargs)

    async def handle_event(
        self, event_type: EventType, *args: Any, **kwargs: Any
    ) -> None:
        """
        Method called when an event is to be dispatched/handled. This arguments expects
        any additional positional/keyword arguments required when triggering the
        callback.

        :param event_type: Event type to dispatch
        :param args: Positional arguments to be passed into the callback before any
            pre-configured positional arguments.
        :param kwargs: Keyword arguments to be passed when triggering the callback.
            These override any pre-configured arguments.
        """
        warnings.warn(
            "CallbackRegistry.handle_event() is deprecated in favour of "
            "CallbackRegistry.dispatch() and will be removed in a future version",
            category=DeprecationWarning,
            stacklevel=2,
        )
        return self.dispatch(event_type, *args, **kwargs)
