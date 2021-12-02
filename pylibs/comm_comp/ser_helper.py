#!/bin/python3
#
#  Copyright (c) 2019-2021.  SandboxZilla
#
#  Permission is hereby granted, free of charge, to any person obtaining a copy of this
#  software and associated documentation files (the "Software"), to deal in the Software
#  without restriction, including without limitation the rights to use, copy, modify,
#  merge, publish, distribute, sublicense, and/or sell copies of the Software, and to
#  permit persons to whom the Software is furnished to do so.
#
#  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED,
#  INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A
#  PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
#  HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
#  OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
#  SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#
#

__author__ = "Erol Yesin"

import sys
import time
from datetime import datetime
from pathlib import Path
from threading import Thread
from typing import Any

import serial

from .base_dev_helper import BaseCommDeviceHelper

SERIAL_IN_EVENT = "serIn"
SERIAL_OUT_EVENT = "serOut"


class MockSerial(BaseCommDeviceHelper):
    def __init__(self, port, baud):
        self.is_open = True
        pass

    def __process_input__(self, queue):
        pass

    def _close(self):
        pass

    def open(self):
        pass

    def readline(self, size=1024):
        return "Test data\r\n".encode("asci")

    def write(self, data):
        pass


class SerialHelper(BaseCommDeviceHelper):
    def __init__(self, port: str = None, baud: int = None):

        self.port_name = port
        super(SerialHelper, self).__init__(
            address=port, port=baud, recv_proc=self.__process_input__
        )
        if port is not None:
            self._serport = serial.Serial(
                port=port, baudrate=baud, timeout=4, exclusive=True
            )
        else:
            self._serport = MockSerial(port=port, baud=baud)

    def _send(self, data):
        if not self._serport.is_open:
            self._open()
        self._serport.write(data=data.encode(encoding="ascii"))

    def _recv(self, size=1024):
        if not self._serport.is_open:
            self._open()
        try:
            data = self._serport.readline()
            data = data.decode()
        except:
            data = None
            self.__event[self.RX_EVENT](payload="BAD DATA:")
        return data

    def _open(self):
        if not self._serport.is_open:
            try:
                self._serport.open()
            except serial.serialutil.SerialException as e:
                self.debug_write(
                    topic=self.port_name + " OPEN ERROR",
                    data="Unable to open port. Error Code : " + str(e),
                )
                print(
                    self.port_name
                    + " OPEN ERROR: Unable to open port. Error: "
                    + str(e)
                )
                super(SerialHelper, self).close()

    def _close(self):
        if self._serport.is_open:
            self._serport.close()
        return self

    def debug_on(self):
        if self.debug_file is None:
            super(SerialHelper, self).debug_on(file_name="ser_helper_debug.log")


if __name__ == "__main__":
    from log_wrapper.log_wrapper import LoggerWrapper

    log = LoggerWrapper(name="ser_sniffer.log")
    p0 = "/dev/ttyUSB0"
    p1 = "/dev/ttyUSB1"

    def on_in(pkt):
        data = pkt["payload"]
        if data is not None and len(data) > 0:
            log.info(pkt["dest"] + ":" + data.split("\r\n")[0])
            pkt["cookie"].send(data)

    ser_p1 = SerialHelper(port=p1, baud=115200).open()
    ser_p0 = SerialHelper(port=p0, baud=115200).open()

    ser_p1.debug_off()
    ser_p0.debug_off()
    try:

        ser_p1.start(name="ser_p1", call_back=on_in, cookie=ser_p0)
        ser_p0.start(name="ser_p0", call_back=on_in, cookie=ser_p1)

        while ser_p0.continue_thread and ser_p1.continue_thread:
            time.sleep(10)

    except KeyboardInterrupt as e:
        pass
    finally:
        print("\nRemember me fondly!")
        ser_p0.close()
        ser_p1.close()
