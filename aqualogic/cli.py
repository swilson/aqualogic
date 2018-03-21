"""aqualogic command line test app."""

from core import AquaLogic, Keys, Leds
import zope.event
import socket
import threading
import logging
import sys

logging.basicConfig(level=logging.INFO)

def data_changed(aq):
    print('Pool Temp: {}'.format(aq.pool_temp))
    print('Air Temp: {}'.format(aq.air_temp))
    print('Pump Speed: {}'.format(aq.pump_speed))
    print('Leds: {}'.format(aq.leds()))
    if aq.is_led_enabled(Leds.CHECK_SYSTEM):
        print('Check System: {}'.format(aq.check_system_msg))

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((sys.argv[1], 23))
reader = s.makefile(mode='rb')
writer = s.makefile(mode='wb')

aq = AquaLogic(reader, writer)

zope.event.subscribers.append(data_changed)

reader_thread = threading.Thread(target=aq.data_reader)
reader_thread.start()

while True:
    key = Keys[input()]
    aq.send_key(key)
