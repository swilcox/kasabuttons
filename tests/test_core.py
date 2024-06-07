from dataclasses import dataclass

import pytest
from kasabuttons.configuration import Configuration, DeviceAction
from kasabuttons.core import KasaButtonsCore


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


# TODO: mock kasa device discovery or use dependency injection to handle fake devices
# TODO: mock asyncio.Queue (or use our own queue) to send "events" to the core loop
