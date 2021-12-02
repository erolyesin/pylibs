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

__author__ = "Erol Yesin"
from threading import Condition


class Queue:
    def __init__(self):
        self.items = []
        self.condition = Condition()

    @property
    def empty(self):
        return self.size == 0

    def put(self, item):
        with self.condition:
            if item is not None:
                self.items.insert(0, item)
            self.condition.notify()

    def put_back(self, item):
        if item is not None:
            with self.condition:
                self.items.append(item)
                self.condition.notify()

    def no_wait_get(self):
        if not self.empty:
            return self.get(timeout=0.5)
        return None

    def peek(self, timeout=None):
        with self.condition:
            while self.empty:
                self.condition.wait(timeout=timeout)
                if self.empty:
                    return None
            try:
                end = self.size - 1
                item = self.items[end]
            except IndexError:
                item = None
            return item

    def clear(self):
        with self.condition:
            self.items.clear()
            self.condition.notify()

    def get(self, timeout=None):
        with self.condition:
            while self.empty:
                self.condition.wait(timeout=timeout)
                if self.empty:
                    return None
            try:
                item = self.items.pop()
            except IndexError:
                item = None
        return item

    def cycle(self):
        item = self.no_wait_get()
        if item is not None:
            self.put(item)
        return item

    @property
    def size_of_next(self):
        if self.size > 0:
            return 4 + len(self.items[-1])
        return None

    def type_of_next(self):
        if self.size > 0:
            return type(self.items[-1])
        return None

    @property
    def size(self):
        ret = len(self.items)
        return ret

    def __len__(self):
        return self.size

    def __iadd__(self, item):
        self.put(item)
        return self


class CommQueues(object):
    __instance: object = None

    def __new__(cls):
        if CommQueues.__instance is None:
            CommQueues.__instance = object.__new__(cls)
            CommQueues.__instance.inQ = Queue()
            CommQueues.__instance.outQ = Queue()
            CommQueues.__instance.tokenQ = Queue()
        return CommQueues.__instance
