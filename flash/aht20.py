import time
from micropython import const


class aht20:
    AHT20_ADDRESS = const(0x38)
    AHT20_BUSY_FLAG = const(0x80)
    AHT20_CALIBRATED_FLAG = const(0x08)
    AHT20_POWERON_DELTA = const(40)
    AHT20_MEASURE_DELTA = const(75)
    AHT20_TIME_BETWEEN_READINGS = const(1500)
    # AHT20_INITIALIZE = bytearray(0xBE, 0x08, 0x00)
    # AHT20_TRIGGER_MEASUREMENT = bytearray(0xAD, 0x33, 0x00)

    # def __init__(self, i2c):
    def __init__(self, i2c):
        self._i2c = i2c
        self._buff = bytearray(6)
        self._next_read = time.ticks_add(
            time.ticks_ms(), self.AHT20_POWERON_DELTA)
        self._humidity = None
        self._temperature = None
        self.initialized = self._initialize()

    def _initialize(self):
        time.sleep_ms(20)
        send_buf = bytearray(3)
        # send_buf[0] = 0xBE
        send_buf[0] = 0xE1
        send_buf[1] = 0x08
        send_buf[2] = 0x00
        self._i2c.writeto(self.AHT20_ADDRESS, send_buf)
        while self.state & self.AHT20_BUSY_FLAG:
            time.sleep_ms(2)
        return self.calibrated

    def reset(self):
        send_buf = bytearray(1)
        send_buf[0] = 0xBA
        self._i2c.writeto(self.AHT20_ADDRESS, send_buf)

    @property
    def calibrated(self):
        """The calibrated property."""
        return self.state & self.AHT20_CALIBRATED_FLAG

    def _read_from(self):
        self._i2c.readfrom_into(self.AHT20_ADDRESS, self._buff)

    @property
    def state(self):
        self._read_from()
        return self._buff[0]

    def _take_measurement(self):
        send_buf = bytearray(3)

        send_buf[0] = 0xAC
        send_buf[1] = 0x33
        send_buf[2] = 0x00
        self._i2c.writeto(self.AHT20_ADDRESS, send_buf)
        time.sleep_ms(75)
        while self.state & self.AHT20_BUSY_FLAG:
            time.sleep(1)
        self._read_from()
        scratch = (self._buff[1] << 12) | (
            self._buff[2] << 4) | (self._buff[3] >> 4)
        self._humidity = (scratch * 100) / 0x100000
        scratch = ((self._buff[3] & 0x0F) << 16) | (
            self._buff[4] << 8) | (self._buff[5])
        self._temperature = ((scratch / 0x100000) * 200) - 50

    @property
    def temperature(self):
        if self._temperature is None:
            self._take_measurement()
        if time.ticks_diff(self._next_read, time.ticks_ms()) < 0:
            self._take_measurement()
            self._next_read = time.ticks_add(
                time.ticks_ms(), self.AHT20_MEASURE_DELTA)
        return self._temperature

    @property
    def temperature_f(self):
        if self._temperature is None:
            self._take_measurement()
        if time.ticks_diff(self._next_read, time.ticks_ms()) < 0:
            self._take_measurement()
            self._next_read = time.ticks_add(
                time.ticks_ms(), self.AHT20_MEASURE_DELTA)
        return (self._temperature * 9/5) + 32

    @property
    def humidity(self):
        """The humidity property."""
        if self._humidity is None:
            self._take_measurement()
        if time.ticks_diff(self._next_read, time.ticks_ms()) < 0:
            self._take_measurement()
            self._next_read = time.ticks_add(
                time.ticks_ms(), self.AHT20_MEASURE_DELTA)
        return self._humidity
