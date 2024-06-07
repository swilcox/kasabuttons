from contextlib import asynccontextmanager

from kasa import Device


@asynccontextmanager
async def async_wrapped_device(device: Device):
    try:
        yield device
    finally:
        await device.disconnect()
