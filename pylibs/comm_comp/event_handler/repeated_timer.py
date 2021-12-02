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

__author__ = "Six: https://stackoverflow.com/users/4117209/six"

import time
from threading import Event, Thread
from .event_handler import EventHandler


class RepeatedTimer(Thread):
    """Repeat `function` every `interval` seconds."""

    def __init__(self, **kwargs):
        assert "interval" in kwargs, "interval key not defined"
        assert "target" in kwargs, "target key not defined"
        assert "src" in kwargs, "src key not defined"
        self.__thread_event = Event()
        self.kwargs = kwargs
        self.join_timeout = 2
        self.__dict__.update(kwargs)
        self.__eventer = EventHandler(src=self.src)

        if "start_tm" not in kwargs:
            self.start_tm = time.time()
        super(RepeatedTimer, self).__init__(name=self.src, target=self._target)
        self.__continue = True
        self.start()

    def _target(self):
        while not self.__thread_event.wait(self._time) and self.__continue:
            self.target(**self.kwargs)

    @property
    def _time(self):
        return self.interval - ((time.time() - self.start_tm) % self.interval)

    def stop(self):
        if self.is_alive():
            self.__thread_event.set()
            self.__continue = False
            self.join(timeout=self.join_timeout)
