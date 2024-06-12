import logging
from os import environ
from collections import namedtuple
from queue import SimpleQueue, Empty
import paho.mqtt.client as mqtt

status_queue = SimpleQueue()
keypad_queue = SimpleQueue()

_logger = logging.getLogger(__name__)

_UserData = namedtuple('userdata', ['prefix'])


def publish(stop_event, prefix):
    try:
        client = mqtt.Client()
        client.user_data_set(_UserData(prefix=prefix))
        client.enable_logger(_logger)
        client.on_message = _on_message
        client.on_connect = _on_connect
        client.connect_async(host=environ.get('MQTT_HOST', 'localhost'))
        client.loop_start()

        while not stop_event.is_set():
            try:
                msg = status_queue.get(timeout=1)
                client.publish(topic=prefix + '/status', payload=msg)
            except Empty:
                continue
    finally:
        stop_event.set()


def _on_connect(client, user_data, flags, rc):
    client.subscribe(topic=user_data.prefix + '/keypad', qos=1)


def _on_message(client, user_data, msg):
    keys = str(msg.payload, 'utf-8')
    keypad_queue.put(keys)
