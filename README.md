# KasaButtons

## Overview

This project aims to allow control over Kasa and/or Tapo smart devices (mostly bulbs) using a computer (including Raspberry Pi devices) and a keyboard (especially small macro keyboards).
Future versions, may also include support of GPIO buttons.

## Usage

### Installation

The project can be installed as a python package, `kasabuttons`.

Via `pipx`:

```shell
pipx install kasabuttons
```

Or `rye`:

```shell
rye install kasabuttons
```

Or into you virtual environment using your preferred mechanism for installing python packages.

The *only* installed command is `kasa-buttons`.

### Configuration

`kasa-buttons` expects there to be a `kasabuttons.toml` file or optionally, specified via parameters `--config your_config_file.yaml`. You can specify either a `yaml` or `toml` file. Example configration here will be in `toml` format.

The minimum configuration would be associating one button on a keyboard to one Kasa or Tapo device.

```toml
[[buttons]]
button_text = "b"
device_name = "Smart Bulb"
long_press = "dim-"
short_press = "toggle"
dim_states = [10, 50, 100]
```

The above example configuration configures a device named `Smart Bulb` to be associated with the `b` key on the keyboard. **NOTE:** The `device_name` value must match *exactly* (including case) with the device as it is setup. A short press will toggle the bulb on/off. A long press (greater than half a second), results in dimming the bulb following the dim_states order headed to the left. A setting of `dim+` would change the dim state of the bulb to the right. Currently, the program loops around, so a long press while the bulb is at 10% brightness in the above example, will result in a new brightness of 100%.

Other options:
`discovery_timeout = 10` sets the number of seconds to scan the network for devices. 10 (seconds) is the default value.

Logging configuration:
```toml
[[logging.handlers]]
sink = "ext://sys.stderr"
format = "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"

[[logging.handlers]]
sink = {"()" = "kasabuttons.logging_utils.custom_loki_handler", "url" = "http://my-local-loki-server.local:3100/loki/api/v1/push"}
serialize = true
backtrace = false
```

The above example sets both the default Loguru stderr output as well as sending logs to a local Loki server.

### Environment Configuration / Authentication

Tapo devices require authentication, so if any of your devices are Tapo devices, they will only work correctly if you also provide credentials. These credentials can be provided in the `.toml` file but it's recommended to set them as environment variables or in a .env file.

```shell
KASA_USERNAME=me@example.com
KASA_PASSWORD=your-password-here
```

The program looks only in the current directory when the script is run for both the default `kasabuttons.toml` file as well as the `.env` file if that is the method being used to set these values.

## Development and Testing

This project uses [rye](https://rye.astral.sh/) for dependency and virtual environment management.

Install the dependencies for KasaButtons

```shell
rye sync
```

Run the tests

```shell
rye test
```

**NOTE:** This project has *not* been tested in Windows. Of particular issue: the keyboard handlers need massive amounts of permissions to gain access to keyboard events. It seems unlikely to me that this project will work correctly in WSL/WSL2. It *should* work correctly with the `pynput` keyboard handler under windows but has not been tested.

Run the program

```shell
rye run kasa-buttons
```

This runs the command line tool that starts the async loop. **Note:** you *need* to have set up a `kasabuttons.toml` or `kasabuttons.yaml` file to configure which keys you want to map to which Kasa/Tapo devices. *See configuration section*.
