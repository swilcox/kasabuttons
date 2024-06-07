import asyncio
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from enum import Enum

from loguru import logger
from pynput import keyboard

LONG_PRESS_TIME = timedelta(seconds=0.5)


class ButtonEventType(Enum):
    SHORT_PRESS = 2
    LONG_PRESS = 1


@dataclass
class ButtonEvent:
    long_press: bool
    character: str

    @property
    def event_type(self) -> ButtonEventType:
        if self.long_press:
            return ButtonEventType.LONG_PRESS
        else:
            return ButtonEventType.SHORT_PRESS


class AsyncKeyboardStatus:
    def __init__(self, loop, queue, chars: list | None = None):
        self._loop = loop
        self._queue = queue
        self._keys_to_watch = [keyboard.KeyCode(char=c) for c in chars] if chars else []
        self.keys_down = {}

    @classmethod
    def keyboard_button_handler(cls, chars: list[str]):
        queue = asyncio.Queue()
        loop = asyncio.get_event_loop()
        async_keyboard_status = cls(loop, queue, chars=chars)
        keyboard.Listener(
            on_press=async_keyboard_status.on_press,
            on_release=async_keyboard_status.on_release,
        ).start()
        return queue

    def on_press(self, key):
        try:
            logger.debug("alphanumeric key {0} pressed".format(key.char))
        except AttributeError:
            logger.debug("special key {0} pressed".format(key))
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
        if key == keyboard.Key.esc:
            # Stop listener
            self._loop.call_soon_threadsafe(
                self._queue.put_nowait, ButtonEvent(long_press=False, character="exit")
            )
            return False
        elif key in self._keys_to_watch:
            self._loop.call_soon_threadsafe(
                self._queue.put_nowait,
                ButtonEvent(long_press=long_press, character=key.char),
            )
