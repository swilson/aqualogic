from enum import IntEnum, unique

@unique
class Keys(IntEnum):
    """Key events which can be sent to the unit"""
    # Second word is the same on first down, 0000 every 100ms while holding
    RIGHT = 0x0001
    MENU = 0x0002
    LEFT = 0x0004
    SERVICE = 0x0008
    MINUS = 0x0010
    PLUS = 0x0020
    POOL_SPA = 0x0040
    FILTER = 0x0080
    LIGHTS = 0x0100
    AUX_1 = 0x0200
    AUX_2 = 0x0400
    AUX_3 = 0x0800
    AUX_4 = 0x1000
    AUX_5 = 0x2000
    AUX_6 = 0x4000
    AUX_7 = 0x8000
    # These are only valid for WIRELESS_KEY_EVENTs
    VALVE_3 = 0x00010000
    VALVE_4 = 0x00020000
    HEATER_1 = 0x00040000
    AUX_8 = 0x00080000
    AUX_9 = 0x00100000
    AUX_10 = 0x00200000
    AUX_11 = 0x00400000
    AUX_12 = 0x00800000
    AUX_13 = 0x01000000
    AUX_14 = 0x02000000
