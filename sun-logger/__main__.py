# -*- coding: utf-8 -*-

from .core import InfluxLogger, SunLogger
from .config import PORT, SLAVE_ADDRESS, BAUDRATE, INFLUXDB_URL, INFLUXDB_TOKEN, INFLUX_BUCKET_ID, INFLUX_ORG


def __main__():
    influx_logger = InfluxLogger(
        INFLUXDB_URL, INFLUXDB_TOKEN, INFLUX_ORG, INFLUX_BUCKET_ID)
    sun_logger = SunLogger(influx_logger, PORT, SLAVE_ADDRESS, BAUDRATE)

    try:
        sun_logger.run()
    except Exception as err:
        print(f'Error: {err}')


if __name__ == '__main__':
    __main__()
