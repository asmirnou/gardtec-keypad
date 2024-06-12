#!/usr/bin/env venv/bin/python

import sys
import logging
import threading
from os import environ
from functools import partial
from signal import signal, SIGINT, SIGTERM
from threading import Event
from keypad import Keypad
from mqtt import status_queue, keypad_queue, publish
from queue import Empty
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter


def init_signals(stop_event):
    for s in [SIGINT, SIGTERM]:
        signal(s, partial(lambda se, *_args: se.set(), stop_event))


def init_logs(names, level):
    formatter = logging.Formatter(fmt='%(name)-8s   %(levelname)-8s%(direction)s %(message)s',
                                  datefmt='%Y-%m-%d %H:%M:%S', defaults={'direction': ':'})

    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    handler.setStream(sys.stdout)

    for name in names:
        logger = logging.getLogger(name)
        logger.setLevel(level)
        logger.addHandler(handler)


def run(stop_event):
    logger = logging.getLogger('gardtec')
    logger_in = logging.LoggerAdapter(logger=logger, extra=dict(direction="<"))
    logger_out = logging.LoggerAdapter(logger=logger, extra=dict(direction=">"))

    last_status = ""
    with Keypad(devpath=args.device, address=args.address, stop_event=stop_event) as keypad:
        while not stop_event.is_set():
            try:
                msg = keypad_queue.get(timeout=args.interval)
                logger_in.info(msg)
                keypad.press(msg)
            except Empty:
                pass

            msg = keypad.status()
            if msg == last_status:
                continue
            status_queue.put(msg)
            logger_out.info(msg)
            last_status = msg


if __name__ == '__main__':
    parser = ArgumentParser(description='Gardtec Remote Keypad for Alarm Control Panel GT490X',
                            formatter_class=ArgumentDefaultsHelpFormatter)
    parser.add_argument('-d', '--device', dest='device', metavar='DEVICE', default='/dev/i2c-1',
                        help='I2C device path')
    parser.add_argument('-a', '--address', dest='address', metavar='ADDRESS', type=int, default=0x56,
                        help='device I2C address')
    parser.add_argument('-i', '--interval', dest='interval', metavar='INTERVAL', type=float, default=0.2,
                        help='update interval in seconds')
    parser.add_argument('-l', '--log-level', dest='log_level', metavar='LOG_LEVEL',
                        type=str, choices=['debug', 'info', 'warning', 'error', 'fatal'],
                        default=environ.get('LOG_LEVEL', 'info'), help='log level')
    args = parser.parse_args()

    stop_event = Event()
    try:
        init_signals(stop_event)
        init_logs(['gardtec', 'keypad', 'mqtt'], args.log_level.upper())

        threading.Thread(target=publish, daemon=True, args=(stop_event, 'gardtec')).start()

        run(stop_event)
    finally:
        stop_event.set()
