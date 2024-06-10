from dataclasses import dataclass
from datetime import timedelta
from enum import Enum

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
