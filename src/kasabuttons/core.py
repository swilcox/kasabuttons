import asyncio
import threading
import time

from kasa import Device, DeviceConfig, Discover, KasaException
from loguru import logger

from .buttons import ButtonEvent
from .configuration import Configuration, DeviceAction
from .kasa_utils import async_wrapped_device
from .keyboard_handlers.base_handler import BaseAsyncKeyboardStatus


class KasaButtonsCore:
    def __init__(self, configuration: Configuration):
        self.configuration = configuration
        self._button_actions = {
            button.button_text: button for button in configuration.buttons
        }
        self._button_device_mapping = {}
        self._last_device_config = None
        self._button_queue = None
        self._keyboard_handler_instance = None
        self._update_thread = None
        self._stop_update_thread = False

    def _background_update_task(self):
        """Background thread task to update device list every 15 minutes"""
        while not self._stop_update_thread:
            asyncio.run(self.update_device_list())
            time.sleep(self.configuration.refresh_frequency)  # default is 15 minutes

    @classmethod
    async def create(
        cls, configuration: Configuration, keyboard_handler: BaseAsyncKeyboardStatus
    ):
        """
        async class method to create a new KasaButtonCore instance and
        hydrate the data with calls to async methods like (update_device_list)
        and connecting up with the AsyncKeyboardStatus handler.
        """
        self = cls(configuration)
        self._button_queue, self._keyboard_handler_instance = (
            keyboard_handler.keyboard_button_handler(chars=self._button_actions.keys())
        )
        await self.update_device_list()

        # Start background update thread
        self._update_thread = threading.Thread(
            target=self._background_update_task, daemon=True
        )
        self._update_thread.start()

        return self

    @classmethod
    async def run(
        cls, configuration: Configuration, keyboard_handler: BaseAsyncKeyboardStatus
    ):
        """
        comprehensive method that async sets up a new instance, initializes the device
        list and then enters the loop waiting on events.
        """
        self = await cls.create(
            configuration=configuration, keyboard_handler=keyboard_handler
        )
        await self.loop()

    def _get_device_config(self, character: str) -> DeviceConfig | None:
        """
        gets the correct device configuration based on which character
        or button was pressed.
        """
        device_config = None
        if character in self._button_actions:
            device_config = (
                self._last_device_config
                if self._button_actions[character].device_name == "~LAST~"
                else self._button_device_mapping.get(character)
            )
            if device_config is None:
                logger.warning(
                    f"{self._button_actions[character].device_name} no config"
                )
        return device_config

    async def _perform_action(self, device: Device, button_event: ButtonEvent):
        """
        method that actually calls the appropriate action method based on the button
        event (character and type of event (e.g. short/long press))
        """
        character = button_event.character
        match self._button_actions[character].get_action(button_event):
            case DeviceAction.TOGGLE:
                await self.toggle_device(device)
            case DeviceAction.DIMMINUS | DeviceAction.DIMPLUS:
                await self.dim_device(
                    device,
                    self._button_actions[character].get_action(button_event),
                    self._button_actions[character].dim_states,
                )
            case _:
                logger.warning(f"no action or bad action defined for {button_event}")

    @logger.catch
    async def loop(self):
        """
        The main loop of the core. Loops until the `exit` character (ESC) is pressed.
        """
        while True:
            button_event = await self._button_queue.get()
            if device_config := self._get_device_config(button_event.character):
                try:
                    async with async_wrapped_device(
                        await Device.connect(
                            config=device_config,
                        )
                    ) as device:
                        logger.debug("successfully connected to device")
                        logger.debug(device.state_information)
                        self._last_device_config = device.config
                        await self._perform_action(device, button_event)
                except KasaException:
                    logger.exception("Exception attempting to connect to device")
                except AttributeError:
                    logger.exception("Attribute Error")
            elif button_event.character == "exit":
                logger.debug("received 'exit' character")
                self._stop_update_thread = True
                if self._update_thread:
                    # Wait for the thread to complete its current iteration
                    self._update_thread.join(timeout=2)
                    # If thread is still alive after timeout, we'll let it terminate naturally
                    # since it's a daemon thread
                break

    async def update_device_list(self):
        """
        Method to find/discover all Kasa devices and update the button device
        map (dict) with correct configuration information for subsequent
        re-connection.
        """
        temp_button_device_mapping = {
            button.button_text: None for button in self.configuration.buttons
        }
        # temporary map of device names to buttons
        device_mapping = {
            button.device_name: button.button_text
            for button in self.configuration.buttons
        }
        logger.debug("attempting to discover kasa/tapo devices")
        devices = await Discover.discover(
            credentials=self.configuration.credentials,
            discovery_timeout=self.configuration.discovery_timeout,
        )
        for device in devices.values():
            await device.update()
            logger.debug(f"found device alias: {device.alias}")
            if device.alias in device_mapping:
                logger.debug(f"device matches config: {device.alias}")
                temp_button_device_mapping[device_mapping[device.alias]] = device.config
            await device.disconnect()
        self._button_device_mapping = temp_button_device_mapping
        logger.debug("finished update_device_list")

    async def toggle_device(self, device: Device):
        """
        Method for toggling a device on/off.
        """
        if device.is_off:
            logger.debug(f"attempting to turn_on device: {device.alias}")
            await device.turn_on()
            logger.info(f"turned ON device: {device.alias}")
        else:
            logger.debug(f"attempting to turn_off device: {device.alias}")
            await device.turn_off()
            logger.info(f"turned OFF device: {device.alias}")

    async def dim_device(
        self, device: Device, action: DeviceAction, dim_states: list[int] | None
    ):
        """
        Method to actually dim (set the brightness) of a device if it supports it.
        Cycles through the `dim_states` configuration of the button pressed to
        determine which brightness percentage to set.
        """
        if not dim_states:
            logger.info(f"{device.alias} has no dim_states")
            return
        if not device.state_information.get("Brightness"):
            logger.info(f"{device.alias} appears to not support Brightness/dimming.")
            return
        _dim_states = dim_states.copy()
        try:
            i = _dim_states.index(device.state_information["Brightness"])
        except (ValueError, KeyError):
            # unexpected brightness value
            i = -1 if action == DeviceAction.DIMPLUS else 1
        _dim_states.append(dim_states[0])
        if action == DeviceAction.DIMMINUS:
            _dim_states.insert(0, dim_states[-1])
        increment = 1 if action == DeviceAction.DIMPLUS else 0
        logger.debug(f"attempting to set dim state: {_dim_states[i + increment]}")
        await device.set_brightness(_dim_states[i + increment])
        logger.info(f"set DIM state: {_dim_states[i + increment]}")
