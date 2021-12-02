#!/bin/python3

#
#  Copyright (c) 2021.  SandboxZilla
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
#
#  Permission is hereby granted, free of charge, to any person obtaining a copy of this
#  software and associated documentation files (the "Software"), to deal in the Software
#  without restriction, including without limitation the rights to use, copy, modify,
#  merge, publish, distribute, sublicense, and/or sell copies of the Software, and to
#  permit persons to whom the Software is furnished to do so.
#
#
#
from __future__ import absolute_import

import time

import paramiko
from base_dev_helper import BaseCommDeviceHelper
from comm_queues import Queue as Q


class SSHHelper(BaseCommDeviceHelper):
    def __init__(self, address: str, port: int, username: str, password: str):
        self.host = address
        self.username = username
        self.password = password
        super(SSHHelper, self).__init__(
            address=self.host, port=port, send_proc=self.__process_output__
        )
        self._work_queue = Q()
        self._client = paramiko.SSHClient()
        self._client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    def _send(self, data: str):
        _send_time = time.time_ns()
        _stdin, _stdout, _stderr = self._client.exec_command(data)
        _recv_time = time.time_ns()

        _stdout = _stdout.read().decode().strip()
        _stderr = _stderr.read().decode().strip()
        msg = {
            "host": self.host,
            "cmd": data,
            "stdout": _stdout,
            "stderr": _stderr,
            "send_time": _send_time,
            "rtt": _recv_time - _send_time,
        }
        self._work_queue.put(item=msg)

    def _recv(self, size=1024):
        return self._work_queue.get(timeout=0.5)

    def _open(self):
        self._client.connect(
            hostname=self.host, username=self.username, password=self.password
        )

    def _close(self):
        self._client.close()


if __name__ == "__main__":
    from itertools import cycle

    ssh_srv = "192.168.0.121"
    user = "surreal"
    passwd = "sSd8kCGNq65e"
    cycle_cmds = cycle(["/opt/surreal/Utilities/vrstool --help"])

    def next_cmd():
        return next(cycle_cmds)

    def on_in(pkt):
        data = pkt["payload"]
        if data is not None and len(data) > 0:
            # log.info(str(data))
            pass

    comm_obj = (
        SSHHelper(address=ssh_srv, port=22, username=user, password=passwd)
        .start(name="sshHelper_utest", call_back=on_in)
        .open()
    )
    try:
        while comm_obj.continue_thread:
            comm_obj.send(next_cmd())
            time.sleep(4)
    except KeyboardInterrupt as e:
        print("\nRemember me fondly!")
    finally:
        comm_obj.close()
