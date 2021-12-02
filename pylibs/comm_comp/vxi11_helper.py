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

import time
from typing import Any

import vxi11

from .base_dev_helper import BaseCommDeviceHelper


class VXI11Helper(BaseCommDeviceHelper):
    def __init__(self, address: str):
        super(VXI11Helper, self).__init__(
            address=address, port="VXI11", recv_proc=self.__process_input__
        )
        self.EOL = "\n"
        self.instrument = vxi11.Instrument(address)

    def _send(self, data):
        if data is None:
            return
        data = str(data)
        if all(eol not in data for eol in self.EOLL):
            data += self.EOL
        self.instrument.write(message=data, encoding="ascii")

    def _recv(self, size=1024):
        return self.instrument.read(num=size, encoding="ascii")

    def _open(self):
        # self.instrument.timeout = None
        # self.instrument.lock_timeout = None
        self.instrument.open()
        self.instrument.client.sock.settimeout(None)
        pass

    def _close(self):
        self.instrument.close()


if __name__ == "__main__":
    from log_wrapper.log_wrapper import LoggerWrapper

    # instr = vxi11.Instrument("TCPIP::192.168.0.135::INSTR")
    # print(instr.ask("*IDN?", encoding='ascii'))

    log = LoggerWrapper(name="vxi11.log")
    payload = "*IDN?"

    def on_in(pkt):
        data = pkt["payload"]
        cookie: VXI11Helper = pkt["cookie"]
        if data is not None and len(data) > 0:
            log.info(data.replace("\n", ""))
            cookie.send(payload)

    inst_obj = VXI11Helper(address="TCPIP::192.168.0.135::INSTR")
    inst_obj.start(name="VXI11Helper_utest", call_back=on_in, cookie=inst_obj)
    inst_obj.open()

    try:
        while inst_obj.continue_thread:
            # log.info(payload)
            # inst_obj.send(payload)
            time.sleep(5)
    except KeyboardInterrupt as e:
        print("\nRemember me fondly!")
    finally:
        inst_obj.close()
