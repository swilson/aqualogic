from enum import Enum, unique
import binascii
import logging

_LOGGER = logging.getLogger(__name__)

@unique
class Leds(Enum):
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
class Keys(Enum):
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

    def __init__(self, stream):
        self._stream = stream
        self._is_metric = False
        self._air_temp = None
        self._pool_temp = None
        self._spa_temp = None
        self._pool_chlorinator = None
        self._spa_chlorinator = None
        self._salt_level = None
        self._leds = 0

    def data_reader(self):
        while True:
            b = self._stream.read(1)

            while True:
                # Search for FRAME_DLE + FRAME_STX
                if not b:
                    return
                if b[0] == self.FRAME_DLE:
                    next_b = self._stream.read(1)
                    if not next_b:
                        return
                    if next_b[0] == self.FRAME_STX:
                        break
                    else:
                        continue
                b = self._stream.read(1)

            frame = bytearray()
            b = self._stream.read(1)

            while True:
                if not b:
                    return
                if b[0] == self.FRAME_DLE:
                    # Should be FRAME_ETX or 0 according to
                    # the AQ-CO-SERIAL manual
                    next_b = self._stream.read(1)
                    if not next_b:
                        return
                    if next_b[0] == self.FRAME_ETX:
                        break
                    elif next_b[0] != 0:
                        # Error?
                        pass

                frame.append(b[0])
                b = self._stream.read(1)
            
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
                continue
            elif frame_type == self.FRAME_TYPE_KEY_EVENT:
                _LOGGER.debug("Key: %s", binascii.hexlify(frame))
            elif frame_type == self.FRAME_TYPE_LEDS:
                _LOGGER.debug("LEDs: %s", binascii.hexlify(frame))
                self._leds = int.from_bytes(frame[0:4], byteorder='little')
                for led in Leds:
                    if led.value & self._leds != 0:
                        _LOGGER.debug(led)
            elif frame_type == self.FRAME_TYPE_DISPLAY_UPDATE:
                parts = frame.decode('latin-1').split()
                _LOGGER.debug('Display update: %s', parts)

                try: 
                    if parts[0] == 'Pool' and parts[1] == 'Temp':
                        # Pool Temp <temp>°[C|F]
                        self._pool_temp = int(parts[2][:-2])
                    elif parts[0] == 'Spa' and parts[1] == 'Temp':
                        # Spa Temp <temp>°[C|F]
                        self._spa_temp = int(parts[2][:-2])
                    elif parts[0] == 'Air' and parts[1] == 'Temp':
                        # Air Temp <temp>°[C|F]
                        self._air_temp = int(parts[2][:-2])
                    elif parts[0] == 'Pool' and parts[1] == 'Chlorinator':
                        # Pool Chlorinator <value>%
                        self._pool_chlorinator = int(parts[2][:-1])
                    elif parts[0] == 'Spa' and parts[1] == 'Chlorinator':
                        # Spa Chlorinator <value>%
                        self._spa_chlorinator = int(parts[2][:-1])
                    elif parts[0] == 'Salt' and parts[1] == 'Level':
                        # Salt Level <value> [g/L|PPM|
                        self._salt_level = float(parts[2])
                        self._is_metric = parts[3] == 'g/L'
                except ValueError:
                    pass
            else:
                _LOGGER.debug("Unknown frame: %s", frame)

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
        """Returns the current pool chlorinator level in %, or None if unknown."""
        return self._pool_chlorinator

    @property
    def spa_chlorinator(self):
        """Returns the current spa chlorinator level in %, or None if unknown."""
        return self._spa_chlorinator
    
    @property
    def salt_level(self):
        """Returns the current salt level, or None if unknown."""
        return self._salt_level

    @property
    def is_metric(self):
        """Returns True if the temperature and salt level values are in Metric."""
        return self._is_metric

    def is_led_enabled(self, led):
        """Returns True if the specified LED is enabled."""
        return (led.value & self._leds) != 0

