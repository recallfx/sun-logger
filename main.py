# -*- coding: utf-8 -*-

import time
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import ASYNCHRONOUS
import minimalmodbus
import RPi.GPIO as GPIO
import functools

from config import PORT, SLAVE_ADDRESS, BAUDRATE, MAX485_DERE, INFLUXDB_URL, INFLUXDB_TOKEN, INFLUX_BUCKET_ID, INFLUX_ORG

def retry_decorator(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        retry_count = 160
        result = None

        while result == None and retry_count > 0:
            try:
                result = func(*args, **kwargs)
            except Exception as err:
                print('.', end ="")
                # time.sleep(0.3)
                retry_count -= 1
                if retry_count == 0:
                    print("Error: {0}".format(err))
        print()
        return result
    return wrapper

class InfluxLogger:
    def __init__(self, url, token, org, bucket_id='sun2000'):
        self.url = url
        self.token = token
        self.org = org
        self.bucket_id = bucket_id
        self.client = InfluxDBClient(url=self.url, token=self.token, org=self.org)

        self.write_api = self.client.write_api(write_options=ASYNCHRONOUS)

    def write(self, data):
        self.write_api.write(self.bucket_id, self.org, data)


class SunLogger:
    def __init__(self, influx_logger, port, slave_address = 1, baudrate = 9600, ts_pin = None, gpio = GPIO):
        self.influx_logger = influx_logger
        self.port = port
        self.slave_address = slave_address
        self.baudrate = baudrate
        self.ts_pin = ts_pin
        self.gpio = gpio

        if (gpio != None):
            self.setup_gpio()

        self.setup_modbus()

    def setup_gpio(self):
        self.gpio.setwarnings(False)

        self.gpio.setmode(GPIO.BOARD)
        self.gpio.setup(self.ts_pin, GPIO.OUT, initial=GPIO.LOW)

    def before_tx_callback(self):
        if (self.ts_pin != None):
            self.gpio.output(self.ts_pin, GPIO.HIGH)
            time.sleep(0.1)

    def after_tx_callback(self):
        if (self.ts_pin != None):
            self.gpio.output(self.ts_pin, GPIO.LOW)

    def setup_modbus(self):
        self.instrument = minimalmodbus.Instrument(
            self.port,
            self.slave_address,
            cb1=self.before_tx_callback,
            cb2=self.after_tx_callback
        )

        #self.instrument.debug = True
        self.instrument.serial.baudrate = self.baudrate
        self.instrument.serial.timeout = 0.2
        #self.instrument.handle_local_echo = True
        #self.instrument.close_port_after_each_call = False
        #self.instrument.precalculate_read_size = True

    @retry_decorator
    def get_model(self):
        return str(self.instrument.read_string(30000, 15))

    @retry_decorator
    def get_model_id(self):
        return self.instrument.read_register(30070)

    @retry_decorator
    def get_pv_strings_number(self):
        return self.instrument.read_register(30071)

    @retry_decorator
    def get_pv_voltage(self, pv_string_no):
        return self.instrument.read_register(32014 + 2 * pv_string_no, 1, signed=True)

    @retry_decorator
    def get_pv_current(self, pv_string_no):
        return self.instrument.read_register(32015 + 2 * pv_string_no, 2, signed=True)

    @retry_decorator
    def get_phase_a_voltage(self):
        return self.instrument.read_register(32069, 1)

    @retry_decorator
    def get_phase_b_voltage(self):
        return self.instrument.read_register(32070, 1)

    @retry_decorator
    def get_phase_c_voltage(self):
        return self.instrument.read_register(32071, 1)

    @retry_decorator
    def get_phase_a_current(self):
        return self.instrument.read_register(32072, 3, signed=True)

    @retry_decorator
    def get_phase_b_current(self):
        return self.instrument.read_register(32074, 3, signed=True)

    @retry_decorator
    def get_phase_c_current(self):
        return self.instrument.read_register(32076, 3, signed=True)

    @retry_decorator
    def get_input_power(self):
        return self.instrument.read_long(32064, 3, signed=True)

    @retry_decorator
    def get_active_power(self):
        return self.instrument.read_long(32080, 3, signed=True)

    @retry_decorator
    def get_reactive_power(self):
        return self.instrument.read_long(32082, 3, signed=True)

    @retry_decorator
    def get_power_factor(self):
        return self.instrument.read_register(32084, 3, signed=True)

    @retry_decorator
    def get_efficiency(self):
        return self.instrument.read_register(32086, 2)

    @retry_decorator
    def get_internal_temp(self):
        return self.instrument.read_register(32087, 1, signed=True)

    def get_device_status_string(self, status):
        switcher = {
                0x0000: 'Standby: initializing',
                0x0001: 'Standby: detecting insulation resistance',
                0x0002: 'Standby: detecting irradiation',
                0x0003: 'Standby: drid detecting',
                0x0100: 'Starting',
                0x0200: 'On-grid (Off-grid mode: running)',
                0x0201: 'Grid connection: power limited (Off-grid mode: running: power limited)',
                0x0202: 'Grid connection: self-derating (Off-grid mode: running: self-derating)',
                0x0300: 'Shutdown: fault',
                0x0301: 'Shutdown: command',
                0x0302: 'Shutdown: OVGR',
                0x0303: 'Shutdown: communication disconnected',
                0x0304: 'Shutdown: power limited',
                0x0305: 'Shutdown: manual startup required',
                0x0306: 'Shutdown: DC switches disconnected',
                0x0307: 'Shutdown: rapid cutoff',
                0x0308: 'Shutdown: input underpower',
                0x0401: 'Grid scheduling: cos F-P curve',
                0x0402: 'Grid scheduling: Q-U curve',
                0x0403: 'Grid scheduling: PF-U curve',
                0x0404: 'Grid scheduling: dry contact',
                0x0405: 'Grid scheduling: Q-P curve',
                0x0500: 'Spot-check ready',
                0x0501: 'Spot-checking',
                0x0600: 'Inspecting',
                0x0700: 'AFCI self check',
                0x0800: 'I-V scanning',
                0x0900: 'DC input detection',
                0x0A00: 'Running: off-grid charging',
                0xA000: 'Standby: no irradiation'
            }
        return switcher.get(status, "Invalid status")

    @retry_decorator
    def get_device_status(self):
        return self.instrument.read_register(32089)

    def _format_line(self, measurement, data):
        fields = ','.join("{!s}={!r}".format(key,val) for (key,val) in data.items())

        return f'{measurement},location=lt {fields} {int(time.time())}'

    def log_device(self, **kwargs):
        line = self._format_line('device', kwargs)

        print(line)

        self.influx_logger.write(line)

    def log_electricity(self, **kwargs):
        line = self._format_line('electricity', kwargs)

        print(line)

        self.influx_logger.write(line)

    def run(self):
        print('Initialising...')

        self.model_id = self.get_model_id()
        print(f'Model ID: {self.model_id}')

        self.model = self.get_model().rstrip('\x00')
        print(f'Model: {self.model}')

        self.pv_string_count = self.get_pv_strings_number()
        print(f'PV String count: {self.pv_string_count}')

        self.log_device(
            model_id=self.model_id,
            model=self.model,
            pv_string_count=self.pv_string_count
        )

        self.device_status_code = None
        self.device_status_string = None
        self.internal_temp = None

        while True:
            device_status_code = self.get_device_status()
            device_status_string = self.get_device_status_string(self.device_status_code)
            internal_temp = self.get_internal_temp()

            if (self.device_status_code != device_status_code):
                self.device_status_code = device_status_code
                self.device_status_string = device_status_string

                print(f'Device status: {self.device_status_string}')

            if (self.internal_temp != internal_temp):
                self.internal_temp = internal_temp

                print(f'Device temperature: {self.internal_temp}')

            pv = {}

            for pv_string_no in range(self.pv_string_count):
                pv[f'pv{pv_string_no}_voltage'] = self.get_pv_voltage(pv_string_no + 1)
                pv[f'pv{pv_string_no}_current'] = self.get_pv_current(pv_string_no + 1)

            phase_a_voltage = self.get_phase_a_voltage()
            phase_b_voltage = self.get_phase_b_voltage()
            phase_c_voltage = self.get_phase_c_voltage()
            phase_a_current = self.get_phase_a_current()
            phase_b_current = self.get_phase_b_current()
            phase_c_current = self.get_phase_c_current()

            input_power = self.get_input_power()
            active_power = self.get_active_power()
            reactive_power = self.get_reactive_power()
            power_factor = self.get_power_factor()
            efficiency = self.get_efficiency()

            self.log_electricity(
                **pv, 
                phase_a_voltage=phase_a_voltage,
                phase_a_current=phase_a_current,
                phase_b_voltage=phase_b_voltage,
                phase_b_current=phase_b_current,
                phase_c_voltage=phase_c_voltage,
                phase_c_current=phase_c_current,
                input_power=input_power,
                active_power=active_power,
                reactive_power=reactive_power,
                power_factor=power_factor,
                efficiency=efficiency,
                internal_temp=self.internal_temp,
                status_code=self.device_status_code,
                status_string=self.device_status_string
            )

if __name__ == '__main__':
    influx_logger = InfluxLogger(INFLUXDB_URL, INFLUXDB_TOKEN, INFLUX_ORG, INFLUX_BUCKET_ID)
    sun_logger = SunLogger(influx_logger, PORT, SLAVE_ADDRESS, BAUDRATE, MAX485_DERE)

    try:
        sun_logger.run()
    except Exception as err:
        print(f'Error: {err}')

