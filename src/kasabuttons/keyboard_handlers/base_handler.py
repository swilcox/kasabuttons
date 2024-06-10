import asyncio
from datetime import UTC, datetime

from loguru import logger

from ..buttons import LONG_PRESS_TIME, ButtonEvent


class BaseAsyncKeyboardStatus:
    """
    This is the Base class for AsyncKeyboardStatus and it can also
    be used a dummy handler for testing.
    """

    def __init__(self, loop, queue, chars: list | None = None):
        self._loop = loop
        self._queue = queue
        self._keys_to_watch = chars if chars else []
        self.keys_down = {}

    @classmethod
    def keyboard_button_handler(cls, chars: list[str]):
        """
        the classmethod for setting things up correctly when dealing with
        asyncio and stuff like that.
        """
        queue = asyncio.Queue()
        loop = asyncio.get_event_loop()
        async_keyboard_status = cls(loop, queue, chars=chars)
        # register a hook or engage the listener in a separate thread here
        return queue, async_keyboard_status

    def on_press(self, key):
        logger.debug(f"key {key} pressed")
        if key not in self.keys_down:
            self.keys_down[key] = datetime.now(UTC)

    def on_release(self, key):
        logger.debug("{0} released".format(key))
        long_press = False
        try:
            press_time = self.keys_down.pop(key)
            down_time = datetime.now(UTC) - press_time
            logger.debug(f"{key} was pressed for: {down_time}")
            if down_time >= LONG_PRESS_TIME:
                long_press = True
        except KeyError:
            logger.debug(f"{key} wasn't in keys_down")
        if key == "Esc":
            self._loop.call_soon_threadsafe(
                self._queue.put_nowait, ButtonEvent(long_press=False, character="exit")
            )
            return False
        elif key in self._keys_to_watch:
            self._loop.call_soon_threadsafe(
                self._queue.put_nowait,
                ButtonEvent(long_press=long_press, character=key),
            )
