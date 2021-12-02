#!/bin/python3

__author__ = "Erol Yesin"

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

from event_handler import EventHandler
from repeated_timer import RepeatedTimer


class TimerEvent(EventHandler, RepeatedTimer):
    def __init__(self, **kwargs):
        assert "interval" in kwargs, "interval key not defined"
        if "event" not in kwargs:
            kwargs["event"] = str(kwargs["interval"]) + "s_timer"
        if "src" not in kwargs:
            kwargs["src"] = "TimerEvent"
        if "target" not in kwargs:
            kwargs["target"] = "self"

        super(TimerEvent, self).__init__(**kwargs)


if __name__ == "__main__":
    import time
    from log_wrapper.log_wrapper import LoggerWrapper

    log = LoggerWrapper(name="test_timer_event.log")

    def on_proc(pkt):
        if pkt is not None:
            log.info(pkt["dest"] + ":" + str(pkt))

    te = TimerEvent(interval=3, target=on_proc)

    try:
        te.subscribe(name="timer_event_test", on_event=on_proc)

        _continue = True
        while _continue:
            time.sleep(2)

    except KeyboardInterrupt as e:
        _continue = False
        print("\nRemember me fondly!")
    finally:
        te.stop()
