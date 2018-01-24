# -*- coding: utf-8 -*-

from .context import aqualogic
from io import FileIO
import pytest

class TestAquaLogic(object):
    def test_basic(self):
        stream = FileIO('tests/data/pool_on.bin')
        aq = aqualogic.AquaLogic(stream)
        aq.data_reader()
        # Yes it was cold out when I grabbed this data
        assert aq.air_temp == -6
        assert aq.pool_temp == -7
        assert aq.chlorinator == None
        assert aq.is_led_enabled(aqualogic.Leds.POOL)
        assert aq.is_led_enabled(aqualogic.Leds.FILTER)
        assert not aq.is_led_enabled(aqualogic.Leds.SPA)
