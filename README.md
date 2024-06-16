# KasaButtons

## Overview

This project aims to allow control over Kasa and/or Tapo smart devices (mostly bulbs) using a computer (including Raspberry Pi devices) and a keyboard (especially small macro keyboards).
Future versions, may also include support of GPIO buttons.

## Installation

**TODO:** Instructions need to be added here...

## Development and Testing

This project uses (rye)[https://rye.astral.sh/] for dependency and virtual environment management.

Install the dependencies for KasaButtons

```shell
rye sync
```

Run the tests

```shell
rye test
```

**NOTE:** This project has not been tested in Windows. Of particular issue: the keyboard handlers need massive amounts of permissions to gain access to keyboard events. It seems unlikely to me that this project will work correctly in WSL/WSL2. It *should* work correctly with the `pynput` keyboard handler under windows but has not been tested.

Run the program

```shell
rye run kasa-buttons
```

This runs the command line tool that starts the async loop. **Note:** you *need* to have set up a `kasabuttons.toml` or `kasabuttons.yaml` file to configure which keys you want to map to which Kasa/Tapo devices.
