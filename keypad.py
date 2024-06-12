from periphery import I2C


class Keypad(object):
    """Wraps all low-level I2C communications (actual read/write operations)
    """

    def __init__(self, devpath, address: int, stop_event):
        self.__i2c = I2C(devpath)
        self.__address = address
        self.__stop_event = stop_event

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.__i2c.close()

    def status(self):
        data = bytearray(32)
        msgs = [I2C.Message(data, read=True)]
        self.__i2c.transfer(self.__address, msgs)
        return str(msgs[0].data[:16], 'ascii', errors='ignore') + \
               '\n' + \
               str(msgs[0].data[16:], 'ascii', errors='ignore')

    def press(self, keys: str):
        data = [int(c, 16) for c in keys if c in '0123456789AB']
        msgs = [I2C.Message(data, read=False)]
        self.__i2c.transfer(self.__address, msgs)
