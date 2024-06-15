import asyncio
import platform

import click
from loguru import logger
from loguru_config import LoguruConfig

from .configuration import Configuration
from .core import KasaButtonsCore

if platform.system().lower() == "darwin":
    from .keyboard_handlers.pynput_handler import (
        PynputAsyncKeyboardStatus as AsyncKeyboardStatus,
    )
else:
    from .keyboard_handlers.keyboard_handler import (
        KeyboardAsyncKeyboardStatus as AsyncKeyboardStatus,
    )


DEFAULT_CONFIG = "kasabuttons.toml"


@click.command()
@click.version_option()
@click.option(
    "--config",
    default=DEFAULT_CONFIG,
    help=f"name of the configuration file (default: {DEFAULT_CONFIG})",
)
def main(config):
    logger.info("kasabuttons CLI Started")
    logger.debug(f"config filename set to: {config}")
    configuration = Configuration.load_from_file(config)
    if configuration.logging:
        LoguruConfig.load(configuration.logging.model_dump())
    logger.debug(f"configuration: {configuration}")
    asyncio.run(
        KasaButtonsCore.run(
            configuration=configuration, keyboard_handler=AsyncKeyboardStatus
        )
    )
    logger.info("kasabuttons CLI Exiting")
