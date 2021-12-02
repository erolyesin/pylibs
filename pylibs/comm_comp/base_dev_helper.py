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
from __future__ import absolute_import

__author__ = "Erol Yesin"

from abc import ABC, abstractmethod
from threading import Thread
from typing import Any, List

from comm_queues.comm_queue import Queue as Q
from event_handler.event_handler import EventHandler as Eventer
from log_wrapper.log_wrapper import LoggerWrapper


class BaseCommDeviceHelper(ABC):
    EOLL: List[str] = ["\r\n", "\n"]
    EOL = "\r\n"

    def __init__(
        self,
        address: str = None,
        port: (int, str, None) = None,
        timeout: int = None,
        recv_proc: callable = None,
        send_proc: callable = None,
        dist_proc: callable = None,
    ):

        self.name = self.__class__.__name__
        self.RX_EVENT = self.name + "InEvent"
        self.TX_EVENT = self.name + "OutEvent"

        self.__event = {
            self.RX_EVENT: Eventer(event=self.RX_EVENT, src=self.name),
            self.TX_EVENT: Eventer(event=self.TX_EVENT, src=self.name),
        }

        self.__inQ = Q()
        self.__outQ = Q()

        self.continue_thread = True
        label = self.name[:3].lower()
        if recv_proc is None:
            recv_proc = self.__process_input__
        self.__inT = Thread(name=label + "IT", target=recv_proc, args=(self.__inQ,))

        if send_proc is None:
            send_proc = self.__process_output__
        self.__outT = Thread(name=label + "OT", target=send_proc, args=(self.__outQ,))

        if dist_proc is None:
            dist_proc = self.__distribute_input__
        self.__distT = Thread(name=label + "DT", target=dist_proc)

        self.debug_file = None
        self.debug_on()
        self.debug_write(
            topic="START " + __name__, data="%s:%s" % (str(address), str(port))
        )

    @classmethod
    @abstractmethod
    def _send(self, data):
        pass

    @classmethod
    @abstractmethod
    def _recv(self, size=1024):
        pass
        return ""

    @classmethod
    @abstractmethod
    def _open(self):
        pass

    @classmethod
    @abstractmethod
    def _close(self):
        pass

    def send(self, data):
        self.__outQ.put(data)

    def subscribe(
        self, name: str, call_back: callable, event: str = None, cookie: Any = None
    ):
        if event is None:
            event = self.RX_EVENT
        self.__event[event].subscribe(name=name, on_event=call_back, cookie=cookie)

    def unsubscribe(self, name: str, event: str = None):
        if event is None:
            event = self.RX_EVENT
        self.__event[event].unsubscribe(name=name)

    def start(
        self, name: str, call_back: callable, event: str = None, cookie: Any = None
    ):
        if event is None:
            event = self.RX_EVENT
        self.subscribe(name=name, call_back=call_back, event=event, cookie=cookie)
        self.__event[event].post(payload="Start logging topic %s to %s" % (event, name))
        return self

    def stop(self, name: str, event: str = None):
        if event is None:
            event = self.RX_EVENT

        self.__event[event].post(payload="Stop logging topic %s to %s" % (event, name))
        self.unsubscribe(event=event, name=name)

    def open(self):
        self.continue_thread = True
        self._open()
        self.__inT.start()
        self.__outT.start()
        self.__distT.start()
        return self

    def close(self):
        self.continue_thread = False
        self._close()
        if self.__inT.is_alive():
            self.__inQ.put(item=None)
            self.__inT.join(timeout=4)
        if self.__outT.is_alive():
            self.__outQ.put(item=None)
            self.__outT.join(timeout=4)
        if self.__distT.is_alive():
            self.__outQ.put(item=None)
            self.__distT.join(timeout=4)
        return self

    def debug_on(
        self,
        file_name=None,
        show_level: bool = False,
        show_thread: bool = False,
        show_module: bool = False,
        show_method: bool = False,
    ):
        if file_name is None:
            file_name = self.name
        if self.debug_file is None:
            if self.debug_file is not None and not self.debug_file.parent.exists():
                self.debug_file.parent.mkdir()
            self.debug_file = LoggerWrapper(
                name=file_name,
                show_level=show_level,
                show_thread=show_thread,
                show_module=show_module,
                show_method=show_method,
            )

            self.debug_write(topic="DEBUG", data="ON")
        self.subscribe(
            name="debug", call_back=self.__dbg_callback__, event=self.RX_EVENT
        )
        self.subscribe(
            name="debug", call_back=self.__dbg_callback__, event=self.TX_EVENT
        )

    def debug_off(self):
        if self.debug_file is not None:
            self.debug_write(topic="DEBUG", data="OFF")
            self.unsubscribe(name="debug", event=self.RX_EVENT)
            self.unsubscribe(name="debug", event=self.TX_EVENT)
        self.debug_file = None
        return self

    def debug_write(self, topic, data):
        if self.debug_file is not None:
            entry = "%s,%s" % (topic, data)
            self.debug_file.info(entry)

    def __dbg_callback__(self, msg):
        if (
            self.debug_file is not None
            and msg is not None
            and msg["payload"] is not None
        ):
            payload = msg["payload"]
            if isinstance(payload, bytes):
                payload = payload.decode("ascii")
            if "\r\n" in payload:
                payload = payload.replace("\r\n", "")
            elif "\n" in payload:
                payload = payload.replace("\n", "")
            self.debug_write(topic=msg["event"], data=payload)

    def __process_input__(self, queue: Q):
        while self.continue_thread:
            data = self._recv()
            if data is not None and len(data) > 0:
                queue.put(item=data)

    def __process_output__(self, queue: Q):
        while self.continue_thread:
            data = queue.get(timeout=5)
            if data is not None:
                self._send(data=data)
                self.__event[self.TX_EVENT](payload=data)

    def __distribute_input__(self):
        while self.continue_thread:
            data = self.__inQ.get(timeout=5)
            if data is not None:
                self.__event[self.RX_EVENT](payload=data)
