"""aqualogic command line test app."""

from core import AquaLogic, Keys, States
import zope.event
import socket
import threading
import logging
import sys

logging.basicConfig(level=logging.INFO)
PORT=23

def data_changed(aq):
    print('Pool Temp: {}'.format(aq.pool_temp))
    print('Air Temp: {}'.format(aq.air_temp))
    print('Pump Speed: {}'.format(aq.pump_speed))
    print('States: {}'.format(aq.states()))
    if aq.get_state(States.CHECK_SYSTEM):
        print('Check System: {}'.format(aq.check_system_msg))

print('Connecting to {}:{}...'.format(sys.argv[1], PORT))
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((sys.argv[1], PORT))
reader = s.makefile(mode='rb')
writer = s.makefile(mode='wb')
print('Connected!')

aq = AquaLogic(reader, writer)

zope.event.subscribers.append(data_changed)

reader_thread = threading.Thread(target=aq.process)
reader_thread.start()

while True:
    line = input()
    try:
        key = Keys[line]
        aq.send_key(key)
    except KeyError:
        print('Invalid key {}'.format(line))
