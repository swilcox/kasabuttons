import os
import tomllib
from enum import Enum
from typing import Optional

import yaml
from kasa import Credentials
from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict

from .buttons import ButtonEvent


class DeviceAction(Enum):
    TOGGLE = "toggle"
    DIMPLUS = "dim+"
    DIMMINUS = "dim-"


class LoggingConfiguration(BaseModel):
    handlers: list[dict]


class ButtonConfiguration(BaseModel):
    button_text: str
    device_name: str
    long_press: DeviceAction
    short_press: DeviceAction
    dim_states: Optional[list[int]] = None

    def get_action(self, button_event: ButtonEvent) -> DeviceAction:
        return self.long_press if button_event.long_press else self.short_press


class Configuration(BaseSettings):
    model_config = SettingsConfigDict(
        extra="ignore", toml_file=["kasabuttons.toml"], env_file=".env"
    )
    buttons: list[ButtonConfiguration]
    refresh_frequency: int = 900  # default to every 15 minutes
    discovery_timeout: int = 10
    kasa_username: str = ""
    kasa_password: str = ""
    logging: Optional[LoggingConfiguration] = None

    @property
    def credentials(self) -> Credentials | None:
        return (
            Credentials(username=self.kasa_username, password=self.kasa_password)
            if self.kasa_username
            else None
        )

    @staticmethod
    def load_from_file(file_name: str):
        file_parts = os.path.splitext(file_name)
        if file_parts[1].lower() in (".toml", ".tml"):
            with open(file_name, "rb") as f:
                return Configuration(**tomllib.load(f))
        elif file_parts[1].lower() in (".yaml", ".yml"):
            with open(file_name, "rb") as f:
                return Configuration(**yaml.load(f, yaml.Loader))
        return Configuration()
