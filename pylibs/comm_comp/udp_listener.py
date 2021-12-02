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

import logging
from socketserver import BaseRequestHandler, UDPServer


LOG_FILE = "logs/syslog_server.log"
HOST, PORT = "0.0.0.0", 2553

#
# NO USER SERVICEABLE PARTS BELOW HERE...
#


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s.%(msecs)03d,%(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    filename=LOG_FILE,
    filemode="a",
)


class SyslogUDPHandler(BaseRequestHandler):
    def handle(self):
        data = bytes.decode(self.request[0].strip())
        # socket = self.request[1]
        print("%s : " % self.client_address[0], str(data))
        logging.info("[%s] %s" % (self.client_address[0], str(data)))


if __name__ == "__main__":
    server = None
    try:
        print("Serving on line %s using port %d...\n" % (HOST, PORT))
        server = UDPServer((HOST, PORT), SyslogUDPHandler)
        server.serve_forever(poll_interval=0.5)
    except (IOError, SystemExit):
        raise
    except KeyboardInterrupt:
        print("Crtl+C Pressed. Shutting down.")
        print("\nRemember me fondly!")
    finally:
        if server is not None:
            server.shutdown()
