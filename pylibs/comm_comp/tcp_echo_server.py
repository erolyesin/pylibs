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
import asyncore
import socket
import time
from log_wrapper.log_wrapper import LoggerWrapper

logging = LoggerWrapper(name="echo_server.log")


# The main purpose of the module is to be a test echo server for other client scripts
class Server(asyncore.dispatcher):

    def __init__(self, host, port):

        self.logger = logging
        asyncore.dispatcher.__init__(self)
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.set_reuse_addr()
        self.bind(('', port))
        self.listen(config.get('SERVER_QUEUE_SIZE', None))
        self.logger.debug('binding to {}'.format(self.socket.getsockname()))

    def handle_accept(self):
        socket, address = self.accept()
        self.logger.debug('new connection accepted from ' + address[0])
        EchoHandler(socket)


class EchoHandler(asyncore.dispatcher_with_send):
    # Read the remote string log it and echo the back the string in upper case
    def handle_read(self):
        msg = self.recv(config.get('RATE', None))
        logging.debug("IN:" + msg.decode('ascii').replace("\r\n", ""))
        self.out_buffer = msg.decode('ascii').upper().encode('ascii')
        if not self.out_buffer:
            self.close()


if __name__ == "__main__":

    config = {
        "HOST": "127.0.0.1",
        "PORT": 5007,
        "RATE": 8096,
        "SERVER_QUEUE_SIZE": 16,
        "SOCKET_AMOUNT": 100}
    try:
        logging.debug('Server start')
        server = Server(config['HOST'], config['PORT'])
        asyncore.loop()
    except KeyboardInterrupt as e:
        logging.debug("Exiting!")
    except:
        logging.error('Something happened, '
                      'if it was not a keyboard break...'
                      'check if address taken, '
                      'or another instance is running. Exit')
    finally:
        print("\nRemember me fondly!")
