"""A library to interface with a Hayward/Goldline AquaLogic/ProLogic 
pool controller."""

from enum import IntEnum, unique
from threading import Timer
import binascii
import logging
import zope.event
import time
import queue

_LOGGER = logging.getLogger(__name__)

@unique
class States(IntEnum):
    """States reported by the unit"""
    # These correspond to the LEDs on the unit
    HEATER_1 = 1 << 0
    VALVE_3 = 1 << 1
    CHECK_SYSTEM = 1 << 2
    POOL = 1 << 3
    SPA = 1 << 4
    FILTER = 1 << 5
    LIGHTS = 1 << 6
    AUX_1 = 1 << 7
    AUX_2 = 1 << 8
    SERVICE = 1 << 9
    AUX_3 = 1 << 10
    AUX_4 = 1 << 11
    AUX_5 = 1 << 12
    AUX_6 = 1 << 13
    VALVE_4 = 1 << 14
    SPILLOVER = 1 << 15
    SYSTEM_OFF = 1 << 16
    AUX_7 = 1 << 17
    AUX_8 = 1 << 18
    AUX_9 = 1 << 19
    AUX_10 = 1 << 20
    AUX_11 = 1 << 21
    AUX_12 = 1 << 22
    AUX_13 = 1 << 23
    AUX_14 = 1 << 24
    SUPER_CHLORINATE = 1 << 25

@unique
class Keys(IntEnum):
    """Key events which can be sent to the unit"""
    # Second word is the same on first down, 0000 every 100ms while holding
    LIGHTS = 0x0001
    AUX_1 = 0x0002
    AUX_2 = 0x0004
    AUX_3 = 0x0008
    AUX_4 = 0x0010
    AUX_5 = 0x0020
    AUX_6 = 0x0040
    AUX_7 = 0x0080
    RIGHT = 0x0100
    MENU = 0x0200
    LEFT = 0x0400
    SYSTEM_OFF = 0x0800
    MINUS = 0x1000
    PLUS = 0x2000
    POOL_SPA = 0x4000
    FILTER = 0x8000

class AquaLogic(object):
    FRAME_DLE = 0x10
    FRAME_STX = 0x02
    FRAME_ETX = 0x03

    FRAME_TYPE_KEY_EVENT = b'\x00\x03'
    FRAME_TYPE_ON_OFF_EVENT = b'\x00\x05'   # Seems to only work for some keys

    FRAME_TYPE_KEEP_ALIVE = b'\x01\x01'
    FRAME_TYPE_LEDS = b'\x01\x02'
    FRAME_TYPE_DISPLAY_UPDATE = b'\x01\x03'
    FRAME_TYPE_PUMP_SPEED = b'\x0c\x01'

    def __init__(self, reader, writer):
        self._reader = reader
        self._writer = writer
        self._is_metric = False
        self._air_temp = None
        self._pool_temp = None
        self._spa_temp = None
        self._pool_chlorinator = None
        self._spa_chlorinator = None
        self._salt_level = None
        self._check_system_msg = None
        self._pump_speed = None
        self._states = 0
        self._send_queue = queue.Queue()

    def check_state(self, data):
        if self.get_state(data['state']) == data['enabled']:
            data['retries'] -= 1
            if data['retries'] != 0:
                # The state hasn't changed; re-queue the request
                self._send_queue.put(data)

    def process(self):
        """Process data; returns when the reader signals EOF."""
        while True:
            b = self._reader.read(1)

            while True:
                # Search for FRAME_DLE + FRAME_STX
                if not b:
                    return
                if b[0] == self.FRAME_DLE:
                    next_b = self._reader.read(1)
                    if not next_b:
                        return
                    if next_b[0] == self.FRAME_STX:
                        break
                    else:
                        continue
                b = self._reader.read(1)

            frame = bytearray()
            b = self._reader.read(1)

            while True:
                if not b:
                    return
                if b[0] == self.FRAME_DLE:
                    # Should be FRAME_ETX or 0 according to
                    # the AQ-CO-SERIAL manual
                    next_b = self._reader.read(1)
                    if not next_b:
                        return
                    if next_b[0] == self.FRAME_ETX:
                        break
                    elif next_b[0] != 0:
                        # Error?
                        pass

                frame.append(b[0])
                b = self._reader.read(1)
            
            # Verify CRC
            frame_crc = int.from_bytes(frame[-2:], byteorder='big')
            frame = frame[:-2]

            calculated_crc = self.FRAME_DLE + self.FRAME_STX
            for b in frame:
                calculated_crc += b
            
            if (frame_crc != calculated_crc):
                logging.warning('Bad CRC')
                continue

            frame_type = frame[0:2]
            frame = frame[2:]

            if frame_type == self.FRAME_TYPE_KEEP_ALIVE:
                # Keep alive
                # If a frame has been queued for transmit, send it.
                if not self._send_queue.empty():
                    data = self._send_queue.get(block=False)
                    self._writer.write(data['frame'])
                    self._writer.flush()
                    _LOGGER.info('Sent: %s', binascii.hexlify(data['frame']))

                    try:
                        if data['state'] != None:
                            # Set a timer to verify the state changes
                            Timer(1.0, self.check_state, [data]).start()
                    except KeyError:
                        pass

                continue
            elif frame_type == self.FRAME_TYPE_KEY_EVENT:
                _LOGGER.info('Key: %s', binascii.hexlify(frame))
            elif frame_type == self.FRAME_TYPE_LEDS:
                _LOGGER.debug('LEDs: %s', binascii.hexlify(frame))
                # First 4 bytes are the LEDs that are on or flashing;
                # second 4 bytes are the LEDs that are flashing
                on = int.from_bytes(frame[0:4], byteorder='little')
                flashing = int.from_bytes(frame[4:8], byteorder='little')
                states = on | flashing
                if states != self._states:
                    self._states = states;
                    zope.event.notify(self)
            elif frame_type == self.FRAME_TYPE_PUMP_SPEED:
                value = int.from_bytes(frame[0:2], byteorder='big')
                if self._pump_speed != value:
                    self._pump_speed = value
                    zope.event.notify(self)
            elif frame_type == self.FRAME_TYPE_DISPLAY_UPDATE:
                parts = frame.decode('latin-1').split()
                _LOGGER.debug('Display update: %s', parts)

                try: 
                    if parts[0] == 'Pool' and parts[1] == 'Temp':
                        # Pool Temp <temp>°[C|F]
                        value = int(parts[2][:-2])
                        if self._pool_temp != value:
                            self._pool_temp = value
                            self._is_metric = parts[2][-1:] == 'C'
                            zope.event.notify(self)
                    elif parts[0] == 'Spa' and parts[1] == 'Temp':
                        # Spa Temp <temp>°[C|F]
                        value = int(parts[2][:-2])
                        if self._spa_temp != value:
                            self._spa_temp = value
                            self._is_metric = parts[2][-1:] == 'C'
                            zope.event.notify(self)
                    elif parts[0] == 'Air' and parts[1] == 'Temp':
                        # Air Temp <temp>°[C|F]
                        value = int(parts[2][:-2])
                        if self._air_temp != value:
                            self._air_temp = value
                            self._is_metric = parts[2][-1:] == 'C'
                            zope.event.notify(self)
                    elif parts[0] == 'Pool' and parts[1] == 'Chlorinator':
                        # Pool Chlorinator <value>%
                        value = int(parts[2][:-1])
                        if self._pool_chlorinator != value:
                            self._pool_chlorinator = value
                            zope.event.notify(self)
                    elif parts[0] == 'Spa' and parts[1] == 'Chlorinator':
                        # Spa Chlorinator <value>%
                        value = int(parts[2][:-1])
                        if self._spa_chlorinator != value:
                            self._spa_chlorinator = value
                            zope.event.notify(self)
                    elif parts[0] == 'Salt' and parts[1] == 'Level':
                        # Salt Level <value> [g/L|PPM|
                        value = float(parts[2])
                        if self._salt_level != value:
                            self._salt_level = value
                            self._is_metric = parts[3] == 'g/L'
                            zope.event.notify(self)
                    elif parts[0] == 'Check' and parts[1] == 'System':
                        # Check System <msg>
                        value = ' '.join(parts[2:])
                        if self._check_system_msg != value:
                            self._check_system_msg = value
                            zope.event.notify(self)
                except ValueError:
                    pass
            else:
                _LOGGER.info('Unknown frame: %s %s', 
                    binascii.hexlify(frame_type), binascii.hexlify(frame))

    def append_data(self, frame, data):
        for c in data:
            frame.append(c)
            if c == self.FRAME_DLE:
                frame.append(0)

    def get_key_event_frame(self, key):
        frame = bytearray()
        frame.append(self.FRAME_DLE)
        frame.append(self.FRAME_STX)

        self.append_data(frame, self.FRAME_TYPE_KEY_EVENT)
        self.append_data(frame, key.value.to_bytes(2, byteorder='big'))
        self.append_data(frame, key.value.to_bytes(2, byteorder='big'))
    
        crc = 0
        for b in frame:
            crc += b
        self.append_data(frame, crc.to_bytes(2, byteorder='big'))

        frame.append(self.FRAME_DLE)
        frame.append(self.FRAME_ETX)

        return frame

    def send_key(self, key):
        """Sends a key."""
        _LOGGER.info('Queueing key %s', key)
        frame = self.get_key_event_frame(key)
        
        # Queue it to send immediately following the reception
        # of a keep-alive packet in an attempt to avoid bus collisions.
        self._send_queue.put({'frame': frame})

    @property
    def air_temp(self):
        """Returns the current air temperature, or None if unknown."""
        return self._air_temp

    @property
    def pool_temp(self):
        """Returns the current pool temperature, or None if unknown."""
        return self._pool_temp
    
    @property
    def spa_temp(self):
        """Returns the current spa temperature, or None if unknown."""
        return self._spa_temp

    @property
    def pool_chlorinator(self):
        """Returns the current pool chlorinator level in %, 
        or None if unknown."""
        return self._pool_chlorinator

    @property
    def spa_chlorinator(self):
        """Returns the current spa chlorinator level in %, 
        or None if unknown."""
        return self._spa_chlorinator
    
    @property
    def salt_level(self):
        """Returns the current salt level, or None if unknown."""
        return self._salt_level
    
    @property
    def check_system_msg(self):
        """Returns the current 'Check System message, or None if unknown."""
        if self.get_state(States.CHECK_SYSTEM):
            return self._check_system_msg
        else:
            return None

    @property
    def pump_speed(self):
        """Returns the current pump speed in percent, or None if unknown."""
        return self._pump_speed

    @property
    def is_metric(self):
        """Returns True if the temperature and salt level values 
        are in Metric."""
        return self._is_metric
    
    def states(self):
        list = []
        """Returns a set containing the enabled states."""
        for e in States:
            if e.value & self._states != 0:
                list.append(e)
        return list

    def get_state(self, state):
        """Returns True if the specified state is enabled."""
        # Check to see if we have a change request pending; if we do
        # return the value we expect it to change to.
        for data in list(self._send_queue.queue):
            if data['state'] == state:
                return not data['enabled']
        return (state.value & self._states) != 0

    def set_state(self, state, enable):
        """Set the state."""

        isEnabled = self.get_state(state)
        if isEnabled == enable:
            return True

        # See if this state has a corresponding Key
        key = None
        try:
            key = Keys[state.name]
        except KeyError:
            # TODO: send the appropriate combination of keys
            # to enable the state
            return False

        frame = self.get_key_event_frame(key)

        # Queue it to send immediately following the reception
        # of a keep-alive packet in an attempt to avoid bus collisions.
        self._send_queue.put({'frame': frame, 'state': state, 
            'enabled': isEnabled, 'retries': 5})

        return True
