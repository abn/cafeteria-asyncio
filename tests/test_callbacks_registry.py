import pytest

from cafeteria.asyncio.callbacks import Callback, CallbackRegistry


def test_callback_registry_simple(mocker):
    callback_one = mocker.Mock()
    callback_two = mocker.Mock()
    registry = CallbackRegistry(callbacks={"one": callback_one, "two": callback_two})
    registry.dispatch("one", "one")
    registry.dispatch("two", "two")
    registry.dispatch(None, "None")

    callback_one.assert_called_once()
    callback_one.assert_called_once_with("one")

    callback_two.assert_called_once()
    callback_two.assert_called_once_with("two")

    callback_one.reset_mock()
    registry.deregister("one", callback_one)
    registry.dispatch("one", "one")

    callback_one.assert_not_called()


def test_callback_registry_multiple(mocker):
    callback_one = mocker.Mock()
    callback_two = mocker.Mock()
    registry = CallbackRegistry(callbacks={"event": [callback_one, callback_two]})

    assert len(registry.callbacks("event")) == 2

    registry.dispatch("event", "event")

    callback_one.assert_called_once()
    callback_one.assert_called_once_with("event")

    callback_two.assert_called_once()
    callback_two.assert_called_once_with("event")

    callback_one.reset_mock()
    callback_two.reset_mock()

    registry.deregister("event", callback_two)
    registry.dispatch("event", "event")

    callback_one.assert_called_once()
    callback_one.assert_called_once_with("event")

    callback_two.assert_not_called()


def test_callback_registry_coro_without_loop(caplog):
    async def hello():
        pass

    registry = CallbackRegistry(callbacks={"hello": hello})

    with pytest.warns(RuntimeWarning):
        registry.dispatch("hello")
        assert "Callback triggered without a running loop" in caplog.text
        assert f"skipping {str(hello)}" in caplog.text


def test_callback_registry_callbacks(mocker):
    callback_one = mocker.Mock()
    callback_two = mocker.Mock()
    callback_default = mocker.Mock()

    registry = CallbackRegistry()
    registry.register("one", callback_one)
    registry.register("two", callback_two)
    registry.register(None, callback_default)

    assert registry.callbacks() == [Callback(callback_default)]
    assert registry.callbacks("one") == [Callback(callback_one)]
    assert registry.callbacks("two") == [Callback(callback_two)]


def test_callback_registry_exists(mocker):
    callback = mocker.Mock()

    registry = CallbackRegistry()
    registry.register("one", callback)

    assert registry.exists("one", callback)
    assert registry.exists("one", Callback(callback))
    assert not registry.exists(None, callback)
    assert not registry.exists("two", callback)


def test_callback_registry_callbacks_default(mocker):
    callback = mocker.Mock()
    registry = CallbackRegistry()

    assert registry.callbacks() == []

    registry.register(None, callback)
    assert registry.callbacks() == [Callback(callback)]


def test_callback_registry_default(mocker):
    callback = mocker.Mock()
    registry = CallbackRegistry()
    registry.register(None, callback)

    registry.dispatch("doesnotexist", "one")

    callback.assert_called_once()
    callback.assert_called_once_with("one")

    callback.reset_mock()
    registry.dispatch(None, "one")

    callback.assert_called_once()
    callback.assert_called_once_with("one")

    callback.reset_mock()
    registry.deregister(None, callback)
    registry.dispatch("doesnotexist", "two")
    registry.dispatch(None, "two")

    callback.assert_not_called()


def test_callback_registry_deregister_non_existing():
    # noinspection PyBroadException
    try:
        CallbackRegistry().deregister("one", lambda x: None)
    except Exception:
        pytest.fail("Unexpected exception")


@pytest.mark.asyncio
async def test_callback_registry_handle_event(mocker):
    callback = mocker.Mock()
    with pytest.warns(DeprecationWarning):
        await CallbackRegistry(callbacks={"one": callback}).handle_event("one", "one")
        callback.assert_called_once_with("one")
