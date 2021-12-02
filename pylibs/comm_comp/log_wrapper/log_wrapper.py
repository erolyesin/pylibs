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

import logging
import sys
import time
from logging.handlers import MemoryHandler
from pathlib import Path

VER = "0.9"


class LoggerWrapper(logging.Logger):
    __instance = None

    def __new__(
        cls,
        name: str = None,
        location: str = None,
        level: int = None,
        show_level: bool = True,
        show_thread: bool = True,
        show_module: bool = True,
        show_method: bool = True,
        date_filename: bool = True,
        console_output: bool = True,
        handlers: logging.handlers = None,
        handler_name: str = None,
    ) -> logging.Logger:
        if LoggerWrapper.__instance is None:
            if name is None:
                name = "app"
                LoggerWrapper.__instance = logging.getLogger(name="")
            else:
                LoggerWrapper.__instance = logging.getLogger(name=name)

            if location is None:
                location = "logs"
            LoggerWrapper.__instance.location = Path(location)

            if not LoggerWrapper.__instance.location.exists():
                LoggerWrapper.__instance.location.mkdir()

            if level is None:
                level = logging.DEBUG

            LoggerWrapper.__instance.setLevel(level=level)
            LoggerWrapper.__instance.name = name
            LoggerWrapper.__instance.formatter = LoggerWrapper.build_formatter(
                show_level=show_level,
                show_thread=show_thread,
                show_module=show_module,
                show_method=show_method,
            )

            if LoggerWrapper.__instance.hasHandlers():
                LoggerWrapper.__instance.handlers.clear()

            if console_output:
                stream_handler = logging.StreamHandler()
                stream_handler.set_name(name=name)
                stream_handler.setFormatter(LoggerWrapper.__instance.formatter)
                LoggerWrapper.__instance.addHandler(stream_handler)

            file_handler = cls.create_file_handler(
                log=LoggerWrapper.__instance,
                name=name,
                show_level=show_level,
                show_thread=show_thread,
                show_module=show_module,
                show_method=show_method,
                date_filename=date_filename,
            )
            # file_handler = logging.FileHandler(file_obj)
            # file_handler.set_name(name=name)
            # file_handler.setFormatter(LoggerWrapper.__instance.formatter)
            LoggerWrapper.__instance.addHandler(file_handler)

        LoggerWrapper.__instance.build_formatter = LoggerWrapper.build_formatter
        LoggerWrapper.__instance.create_file_handler = cls.create_file_handler
        LoggerWrapper.__instance.remove_handler = cls.remove_handler
        LoggerWrapper.__instance.version = LoggerWrapper.version

        if handlers is not None:
            for handler in handlers:
                if isinstance(handler, logging.Handler):
                    LoggerWrapper.__instance.addHandler(handler)

        if handler_name is not None:
            handler = LoggerWrapper.__instance.create_file_handler(
                log=LoggerWrapper.__instance,
                name=handler_name,
                show_level=show_level,
                show_thread=show_thread,
                show_module=show_module,
                show_method=show_method,
                date_filename=date_filename,
            )
            LoggerWrapper.__instance.addHandler(handler)

        return LoggerWrapper.__instance

    @staticmethod
    def build_formatter(
        show_level: bool = True,
        show_thread: bool = True,
        show_module: bool = True,
        show_method: bool = True,
    ):
        """

        @param show_level: bool
        @param show_method: bool
        @param show_module: bool
        @param show_thread: bool
        """
        _format_str = "%(asctime)s.%(msecs)03d,"
        if show_level:
            _format_str += "[%(levelname)s],"
        if show_module or show_method or show_thread:
            _format_str += "["
            if show_thread:
                _format_str += "%(threadName)s"
            if show_module:
                _format_str += ":%(module)s"
            if show_method:
                _format_str += ":%(funcName)s"
            if show_module:
                _format_str += ":%(lineno)d"
            _format_str += "],"
        _format_str += "%(message)s"
        return logging.Formatter(_format_str, datefmt="%Y-%m-%d %H:%M:%S")

    @staticmethod
    def create_file_handler(
        log,
        name: str,
        show_level: bool = True,
        show_thread: bool = True,
        show_module: bool = True,
        show_method: bool = True,
        date_filename: bool = True,
    ):
        for index, handler in enumerate(log.handlers):
            if isinstance(handler, logging.FileHandler) and name == handler.name:
                return handler
        if date_filename:
            file_obj = Path(log.location, name + time.strftime("_%Y%m%d%H%M%S.log"))
        else:
            file_obj = Path(log.location, name + ".log")

        _formatter = LoggerWrapper.build_formatter(
            show_level=show_level,
            show_thread=show_thread,
            show_module=show_module,
            show_method=show_method,
        )

        handler = logging.FileHandler(file_obj)
        handler.set_name(name=name)
        handler.setFormatter(_formatter)
        return handler

    @staticmethod
    def remove_handler(log, name):
        for index, handler in enumerate(log.handlers):
            if handler.name == name:
                log.removeHandler(handler)

    @staticmethod
    @property
    def version():
        return VER


def log_on_error(logger=None, capacity=None):
    if logger is None:
        logger = LoggerWrapper()

    if capacity is None:
        capacity = 100
    mem_handler = MemoryHandler(capacity, flushLevel=logger.level)
    for handler in logger.handlers:
        mem_handler.setTarget(handler)
    logger.addHandler(mem_handler)

    def decorator(fn):
        def wrapper(*args, **kwargs):
            try:
                return fn(*args, **kwargs)
            except KeyboardInterrupt:
                logger.info("Stopping...")
                sys.exit(0)
            except Exception as exp:
                logger.exception("Call Failed", exc_info=exp)
                sys.exit(0)
            finally:
                super(MemoryHandler, mem_handler).flush()
                logger.removeHandler(mem_handler)

        return wrapper

    return decorator
