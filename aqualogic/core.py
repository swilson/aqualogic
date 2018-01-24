from threading import Thread
import re

class AquaLogic(object):
    FRAME_ESCAPE = 0x10
    FRAME_START = 0x02
    FRAME_END = 0x03

    FRAME_TYPE_KEEP_ALIVE = b'\x01\x01'
    FRAME_TYPE_STATUS = b'\x01\x02'
    FRAME_TYPE_DISPLAY_UPDATE = b'\x01\x03'

    def __init__(self, stream):
        self._stream = stream
        self._is_celsius = True
        self._air_temp = None
        self._pool_temp = None
        self._chlorinator = None

    def data_reader(self):
        while True:
            b = self._stream.read(1)

            while True:
                # Search for FRAME_ESCAPE + FRAME_START
                if not b:
                    return
                if b[0] == self.FRAME_ESCAPE:
                    b = self._stream.read(1)
                    if not b:
                        return
                    if b[0] == self.FRAME_START:
                        break
                    else:
                        continue
                b = self._stream.read(1)

            frame = bytearray()
            b = self._stream.read(1)

            while True:
                # Search for FRAME_ESCAPE + FRAME_END
                if not b:
                    return
                if b[0] == self.FRAME_ESCAPE:
                    b = self._stream.read(1)
                    if not b:
                        return
                    if b[0] == self.FRAME_END:
                        break
                    else:
                        # TODO: Is anything else escaped?
                        pass
                frame.append(b[0])
                b = self._stream.read(1)
            
            # Verify CRC
            frame_crc = int.from_bytes(frame[-2:], byteorder='big')
            frame = frame[:-2]

            calculated_crc = self.FRAME_ESCAPE + self.FRAME_START
            for b in frame:
                calculated_crc += b
            
            if (frame_crc != calculated_crc):
                print('Bad CRC')

            print(frame)

            frame_type = frame[0:2]
            frame = frame[2:]

            if frame_type == self.FRAME_TYPE_KEEP_ALIVE:
                # Keep alive
                pass
            elif frame_type == self.FRAME_TYPE_DISPLAY_UPDATE:
                parts = frame.decode('latin-1').split()
                if parts[0] == 'Pool' and parts[1] == 'Temp':
                    # Pool Temp <temp>°[C|F]
                    self._pool_temp = int(parts[2][:-2])
                elif parts[0] == 'Air' and parts[1] == 'Temp':
                    # Air Temp <temp>°[C|F]
                    self._air_temp = int(parts[2][:-2])
                elif parts[0] == 'Pool' and parts[1] == 'Chlorinator':
                    # Pool Chlorinator <value>%
                    self._chlorinator = int(parts[2][:-1])

                print(parts)

    @property
    def air_temp(self):
        return self._air_temp

    @property
    def pool_temp(self):
        return self._pool_temp
    
    @property
    def chlorinator(self):
        return self._chlorinator
    
    @property
    def is_celcius(self):
        return self._is_celcius
