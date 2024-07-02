import tomllib

import pytest
from kasabuttons.configuration import Configuration


def test_good_toml_configuration():
    configuration = Configuration.load_from_file("./tests/fixtures/testconfig.toml")
    assert configuration.logging is not None
    assert len(configuration.buttons) == 1
    assert (
        configuration.buttons[0].button_text == "a"
        and configuration.buttons[0].device_name == "Smart Bulb1"
    )


def test_invalid_toml_configuration():
    # NOTE: for now... program is going to throw TOMLDecodeError exception and exit
    # TODO: decide how we'll more gracefully handle exceptions like this
    with pytest.raises(tomllib.TOMLDecodeError):
        Configuration.load_from_file("./tests/fixtures/testinvalid.toml")


# TODO: tests to write
# test_bad_toml_configuration ... pydantic validation error stuff
# test_good_yaml_configuration
# test_invalid_yaml_configuration
# test_bad_yaml_configuration
# test some additional configuration edge cases like:
# - no buttons (empty list)
