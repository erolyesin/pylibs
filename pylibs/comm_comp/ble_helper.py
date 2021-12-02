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
#

__author__ = "Erol Yesin"

import time

from bluepy.btle import Peripheral
from comm_queues.comm_queue import Queue as Q

from .base_dev_helper import BaseCommDeviceHelper


class BLEHelper(BaseCommDeviceHelper):
    def __init__(self, address: str, port: int):
        super(BLEHelper, self).__init__(
            address=address, port=port, recv_proc=self.__process_input__
        )
        self._device = Peripheral(deviceAddr=address, addrType="random", iface=port)

        services = self._device.getServices()
        for service in services:
            print(service)

        pass

    def __process_input__(self, queue: Q):
        msg = ""
        while self.continue_thread:
            data = self.__recv(size=2)
            if data is not None and len(data) > 0:
                msg += data.decode("ascii")
                if "\r\n" not in msg:
                    continue
                queue.put(item=msg)
                msg = ""

    def __send(self, data):
        self._socket.sendall(str(data).encode("ascii"))

    def __recv(self, size=1024):
        return self._socket.recv(2)

    def __open(self):
        pass

    def __close(self):
        self._socket.shutdown(socket.SHUT_RDWR)
        self._socket.close()


if __name__ == "__main__":
    from log_wrapper.log_wrapper import LoggerWrapper

    log = LoggerWrapper(name="ble.log")

    def on_in(pkt):
        data = pkt["payload"]
        if data is not None and len(data) > 0:
            log.info(str(data))

    comm_obj = (
        BLEHelper(address="55:87:b7:f8:f7:09", port=1)
        .open()
        .start(name="bleHelper_utest", call_back=on_in)
    )
    try:
        while comm_obj.continue_thread:
            payload = 0xD7
            comm_obj.send(payload)
            log.info(str(payload))
            time.sleep(10)
    except KeyboardInterrupt as e:
        print("\nRemember me fondly!")
    finally:
        comm_obj.close()
