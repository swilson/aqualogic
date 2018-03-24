"""A library to interface with a Hayward/Goldline AquaLogic/ProLogic 
pool controller."""

from enum import IntEnum, unique
import binascii
import logging
import zope.event
import time
import queue

_LOGGER = logging.getLogger(__name__)

@unique
class Leds(IntEnum):
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
    # Second word is the same on first down, 0000 every 100ms while holding
    LIGHTS = 0x0001
    AUX_1 = 0x0002
    AUX_2 = 0x0004
    RIGHT = 0x0100
    MENU = 0x0200
    LEFT = 0x0400
    MINUS = 0x1000
    PLUS = 0x2000
    POOL_SPA = 0x4000
    FILTER = 0x8000

class AquaLogic(object):
    FRAME_DLE = 0x10
    FRAME_STX = 0x02
    FRAME_ETX = 0x03

    FRAME_TYPE_KEY_EVENT = b'\x00\x03'

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
        self._leds = 0
        self._send_queue = queue.Queue()

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
                try:
                    send_frame = self._send_queue.get(block=False)
                    self._writer.write(send_frame)
                    self._writer.flush()
                except queue.Empty:
                    pass
                continue
            elif frame_type == self.FRAME_TYPE_KEY_EVENT:
                _LOGGER.info("Key: %s", binascii.hexlify(frame))
            elif frame_type == self.FRAME_TYPE_LEDS:
                _LOGGER.debug("LEDs: %s", binascii.hexlify(frame))
                leds = int.from_bytes(frame[0:4], byteorder='little')
                if leds != self._leds:
                    self._leds = leds;
                    zope.event.notify(self)
                for led in Leds:
                    if led.value & self._leds != 0:
                        _LOGGER.debug(led)
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
                            zope.event.notify(self)
                    elif parts[0] == 'Spa' and parts[1] == 'Temp':
                        # Spa Temp <temp>°[C|F]
                        value = int(parts[2][:-2])
                        if self._spa_temp != value:
                            self._spa_temp = value
                            zope.event.notify(self)
                    elif parts[0] == 'Air' and parts[1] == 'Temp':
                        # Air Temp <temp>°[C|F]
                        value = int(parts[2][:-2])
                        if self._air_temp != value:
                            self._air_temp = value
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
                _LOGGER.info("Unknown frame: %s %s", 
                    binascii.hexlify(frame_type), binascii.hexlify(frame))

    def queue_key(self, key):
        """Queues a key for sending."""
        _LOGGER.info("Sending key %s", key)
        frame = bytearray()
        frame.append(self.FRAME_DLE)
        frame.append(self.FRAME_STX)
        frame.extend(self.FRAME_TYPE_KEY_EVENT)
        frame.extend(key.value.to_bytes(2, byteorder='big'))
        frame.extend(key.value.to_bytes(2, byteorder='big'))
        crc = 0
        for b in frame:
            crc += b
        frame.extend(crc.to_bytes(2, byteorder='big'))
        frame.append(self.FRAME_DLE)
        frame.append(self.FRAME_ETX)

        # Queue it to send immediately following the reception
        # of a keep-alive packet in an attempt to avoid bus collisions.
        # TODO: check LCD output for result and retry if a collision 
        # occurred
        self._send_queue.put(frame)
       
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
        """Returns the current 'Check System message, or None if unknown.
        Only valid when Leds.CHECK_SYSTEM is on."""
        return self._check_system_msg

    @property
    def pump_speed(self):
        """Returns the current pump speed in percent, or None if unknown."""
        return self._pump_speed

    @property
    def is_metric(self):
        """Returns True if the temperature and salt level values 
        are in Metric."""
        return self._is_metric
    
    def leds(self):
        list = []
        """Returns a set containing the enabled LEDs."""
        for e in Leds:
            if e.value & self._leds != 0:
                list.append(e)
        return list

    def is_led_enabled(self, led):
        """Returns True if the specified LED is enabled."""
        return (led.value & self._leds) != 0

