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
#  PARTICULAR PURPOSE AND NONINFINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
#  HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
#  OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
#  SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#
#
from __future__ import absolute_import

__author__ = "Erol Yesin"

import socket
import sys
import time

from base_dev_helper import BaseCommDeviceHelper
from comm_queues import Queue as Q


class TCPHelper(BaseCommDeviceHelper):
    def __init__(self, address: str):

        self.address = address.split(":")[0]
        self.port = int(address.split(":")[1])
        super(TCPHelper, self).__init__(
            address=self.address, port=self.port, recv_proc=self.__process_input__
        )
        try:
            self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._socket.connect((self.address, self.port))
        except socket.error as msg:
            self.debug_write(topic='Error',
                             data="Socket could not be created. Error Code : "
                                  + str(msg[0])
                                  + " Message "
                                  + msg[1]
                             )
            sys.exit()

    def __process_input__(self, queue: Q):
        msg = ""
        while self.continue_thread:
            data = self._recv(size=2)
            if data is not None and len(data) > 0:
                msg += data.decode("ascii")
                if "\r\n" not in msg and "\n" not in msg:
                    continue
                queue.put(item=msg)
                msg = ""

    def _send(self, data):
        data = str(data)
        if data is not None and ("\r\n" not in data and "\n" not in data):
            data += "\r\n"
        data = data.encode()
        self._socket.sendall(data)

    def _recv(self, size=1024):
        return self._socket.recv(2)

    def _open(self):
        pass

    def _close(self):
        self._socket.shutdown(socket.SHUT_RDWR)
        self._socket.close()


# Simple test to verify the TCPPHelper class.
# Sends a simple text message and waits and for response.
# Used with included echo server
# See code for optional parameters, or enter '-h' as a parameter to get help
#   Usage:   >python3 tcp_helper.py -h
if __name__ == "__main__":
    import argparse
    from log_wrapper.log_wrapper import LoggerWrapper
    from event_handler.repeated_timer import RepeatedTimer

    # log folder will be created within the folder the scripts was called from.
    # Each execution instance will generate a dated and timestamped log file.
    # The generated log file format should be the minimum required for all log entries.
    log = LoggerWrapper(name="tcp_helper_test.log")

    parser = argparse.ArgumentParser()
    parser.add_argument('--adr',
                        type=str,
                        default="127.0.0.1:5007",
                        help='Enter address and port of test server. Default: "127.0.0.1:5007"')
    parser.add_argument('--msg',
                        type=str,
                        default="$$hello$$",
                        help='Enter the message to repeat every 10s. Default: "$$hello$$"')
    args = parser.parse_args()

    comm_obj = TCPHelper(address=args.adr)


    # Callback for timed event
    def on_proc(**kwargs):
        log.info(kwargs)

        if 'pkt' in kwargs and kwargs['pkt'] is not None:
            pkt = kwargs['pkt']
            log.info(pkt["dest"] + ":" + str(pkt))
        payload = args.msg
        log.info("OUT:" + payload)
        comm_obj.send(payload)


    te = RepeatedTimer(interval=3, target=on_proc, src='tcp_helper_test', payload=args.msg)


    # Callback when a message is received
    def on_in(pkt):
        data = pkt["payload"]
        if data is not None and len(data) > 0:
            log.info("IN:" + data.replace("\r\n", ""))


    try:
        comm_obj.open().start(name="tcpHelper_utest", call_back=on_in)
        while comm_obj.continue_thread:
            time.sleep(2)
    except KeyboardInterrupt as e:
        print("\nRemember me fondly!")
    finally:
        te.stop()
        comm_obj.close()
