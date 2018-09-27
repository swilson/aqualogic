"""aqualogic command line test app."""

import threading
import logging
import sys
from core import AquaLogic, States

logging.basicConfig(level=logging.INFO)
PORT = 23


def _data_changed(panel):
    print('Pool Temp: {}'.format(panel.pool_temp))
    print('Air Temp: {}'.format(panel.air_temp))
    print('Pump Speed: {}'.format(panel.pump_speed))
    print('Pump Power: {}'.format(panel.pump_power))
    print('States: {}'.format(panel.states()))
    if panel.get_state(States.CHECK_SYSTEM):
        print('Check System: {}'.format(panel.check_system_msg))


PANEL = AquaLogic()
print('Connecting to {}:{}...'.format(sys.argv[1], PORT))
PANEL.connect(sys.argv[1], PORT)
print('Connected!')

READER_THREAD = threading.Thread(target=PANEL.process, args=[_data_changed])
READER_THREAD.start()

while True:
    LINE = input()
    try:
        STATE = States[LINE]
        PANEL.set_state(STATE, not PANEL.get_state(STATE))
    except KeyError:
        print('Invalid key {}'.format(LINE))
