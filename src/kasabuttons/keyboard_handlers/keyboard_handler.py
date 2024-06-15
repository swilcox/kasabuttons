import asyncio
from datetime import UTC, datetime

import keyboard
from loguru import logger

from ..buttons import LONG_PRESS_TIME, ButtonEvent
from .base_handler import BaseAsyncKeyboardStatus


class KeyboardAsyncKeyboardStatus(BaseAsyncKeyboardStatus):
    def __init__(self, loop, queue, chars: list | None = None):
        super().__init__(loop=loop, queue=queue, chars=chars)

    @classmethod
    def keyboard_button_handler(cls, chars: list[str]):
        queue = asyncio.Queue()
        loop = asyncio.get_event_loop()
        async_keyboard_status = cls(loop, queue, chars=chars)
        keyboard.hook(async_keyboard_status.on_event)
        return queue, async_keyboard_status

    def on_event(self, event: keyboard.KeyboardEvent):
        if event.event_type == keyboard.KEY_DOWN:
            self.on_press(event.name)
        elif event.event_type == keyboard.KEY_UP:
            self.on_release(event.name)

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
        if key == "esc":
            self._loop.call_soon_threadsafe(
                self._queue.put_nowait, ButtonEvent(long_press=False, character="exit")
            )
            return False
        elif key in self._keys_to_watch:
            self._loop.call_soon_threadsafe(
                self._queue.put_nowait,
                ButtonEvent(long_press=long_press, character=key),
            )
