from dataclasses import dataclass
import asyncio
from unittest.mock import patch

import pytest
from kasabuttons.buttons import ButtonEvent
from kasabuttons.configuration import Configuration, DeviceAction
from kasabuttons.core import KasaButtonsCore
from kasabuttons.keyboard_handlers.base_handler import BaseAsyncKeyboardStatus


@dataclass
class MockDevice:
    alias: str
    is_off: bool
    state_information: dict

    async def turn_on(self):
        self.is_off = False

    async def turn_off(self):
        self.is_off = True

    async def set_brightness(self, value: int):
        self.state_information["Brightness"] = value

    async def update(self, *args, **kwargs):
        pass

    @classmethod
    async def connect(cls, *args, **kwargs):
        if len(args):
            return cls(**args[0])
        return cls(kwargs)

    async def disconnect(self):
        pass

    @property
    def config(self):
        """property that returns all we need to recreate a new device instance"""
        return {
            "alias": self.alias,
            "is_off": self.is_off,
            "state_information": self.state_information,
        }


class MockDiscover:
    @classmethod
    async def discover(cls, *arg, **kwargs):
        return {
            "mockbulb": MockDevice(
                "mockbulb", is_off=False, state_information={"Brightness": 100}
            ),
            "mockplug": MockDevice("mockplug", is_off=False, state_information={}),
        }


@pytest.fixture
def test_configuration():
    config_data = {
        "buttons": [
            {
                "button_text": "a",
                "device_name": "mockbulb",
                "long_press": "dim+",
                "short_press": "toggle",
                "dim_states": [10, 50, 100],
            },
        ]
    }
    return Configuration(_env_file=None, **config_data)


@pytest.mark.asyncio
async def test_toggle_device(test_configuration):
    core = KasaButtonsCore(configuration=test_configuration)
    mock_device = MockDevice(
        alias="mockbulb", is_off=True, state_information={"Brightness": 10}
    )
    await core.toggle_device(mock_device)
    assert not mock_device.is_off
    await core.toggle_device(mock_device)
    assert mock_device.is_off


@dataclass
class BrightnessTestCase:
    starting_brightness: int
    expected_brightness: int
    action: DeviceAction


@pytest.mark.asyncio
async def test_set_brightness(test_configuration):
    core = KasaButtonsCore(configuration=test_configuration)
    brightness_tests = [
        BrightnessTestCase(10, 50, DeviceAction.DIMPLUS),
        BrightnessTestCase(50, 100, DeviceAction.DIMPLUS),
        BrightnessTestCase(100, 10, DeviceAction.DIMPLUS),
        BrightnessTestCase(10, 100, DeviceAction.DIMMINUS),
        BrightnessTestCase(100, 50, DeviceAction.DIMMINUS),
        BrightnessTestCase(50, 10, DeviceAction.DIMMINUS),
    ]
    for brightness_test in brightness_tests:
        mock_device = MockDevice(
            alias="mockbulb",
            is_off=False,
            state_information={"Brightness": brightness_test.starting_brightness},
        )
        await core.dim_device(mock_device, brightness_test.action, [10, 50, 100])
        assert (
            mock_device.state_information["Brightness"]
            == brightness_test.expected_brightness
        )


@pytest.mark.asyncio
async def test_non_standard_brightness(test_configuration):
    # non-supporting device test
    core = KasaButtonsCore(configuration=test_configuration)
    mock_device = MockDevice(alias="mockplug", is_off=False, state_information={})
    await core.dim_device(mock_device, DeviceAction.DIMPLUS, [10, 50, 100])
    assert "Brightness" not in mock_device.state_information

    # no dim_states set test
    mock_device = MockDevice(
        alias="mockbulb", is_off=False, state_information={"Brightness": 50}
    )
    await core.dim_device(mock_device, DeviceAction.DIMPLUS, [])
    assert mock_device.state_information["Brightness"] == 50

    # non-standard initial brightness
    mock_device = MockDevice(
        alias="mockbulb", is_off=False, state_information={"Brightness": 15}
    )
    await core.dim_device(mock_device, DeviceAction.DIMPLUS, [10, 50, 100])
    assert mock_device.state_information["Brightness"] == 10


@pytest.mark.asyncio
async def test_create_core_and_loop(test_configuration):
    with patch("kasabuttons.core.Discover", MockDiscover):
        core = await KasaButtonsCore.create(
            test_configuration, keyboard_handler=BaseAsyncKeyboardStatus
        )
        assert core is not None
        assert core._update_thread is not None
        assert core._update_thread.is_alive()

        # Test exit cleanup
        core._button_queue.put_nowait(ButtonEvent(long_press=False, character="exit"))
        await core.loop()

        # Verify thread cleanup was initiated
        assert core._stop_update_thread is True
        # Give the thread time to complete its current iteration and terminate
        await asyncio.sleep(
            0.1
        )  # 100ms should be enough since we're not actually waiting 15min in tests


@pytest.mark.asyncio
async def test_mock_connect():
    """just to verify that our mock device config and connect work together properly"""
    m = MockDevice("mydevice", False, {"something": "else"})
    new_m = await MockDevice.connect(m.config)
    assert m.config == new_m.config


# TODO: further mock devices/discover to track devices... essentially mock kasa status
# tests:
# * toggle
# * dim plus and minus
# * ~last~ functionality
