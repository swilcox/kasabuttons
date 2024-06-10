import platform

from loki_logger_handler.loki_logger_handler import LoguruFormatter, LokiLoggerHandler


def custom_loki_handler(url: str = "") -> LokiLoggerHandler:
    return LokiLoggerHandler(
        url=url,
        labels={"application": "kasabuttons", "hostname": platform.node()},
        labelKeys={},
        timeout=10,
        defaultFormatter=LoguruFormatter(),
    )
