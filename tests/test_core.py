# -*- coding: utf-8 -*-

from aqualogic.core import AquaLogic, States
from io import FileIO
import pytest
import logging
import socket

logging.basicConfig(level=logging.DEBUG)

class TestAquaLogic(object):
    def data_changed(self, aq):
        pass

    def test_pool(self):
        aq = AquaLogic()
        aq.connect_io(FileIO('tests/data/pool_on.bin'))
        aq.process(self.data_changed)
        # Yes it was cold out when I grabbed this data
        assert aq.is_metric
        assert aq.air_temp == -6
        assert aq.pool_temp == -7
        assert aq.spa_temp == None
        assert aq.pool_chlorinator == None
        assert aq.spa_chlorinator == 3
        assert aq.salt_level == 3.1
        assert aq.get_state(States.POOL)
        assert aq.get_state(States.FILTER)
        assert not aq.get_state(States.SPA)


    def test_spa(self):
        aq = AquaLogic()
        aq.connect_io(FileIO('tests/data/spa_on.bin'))
        aq.process(self.data_changed)
        assert aq.is_metric
        assert aq.air_temp == -6
        assert aq.pool_temp == None
        assert aq.spa_temp == -7
        assert aq.pool_chlorinator == None
        assert aq.spa_chlorinator == 3
        assert aq.salt_level == 3.1
        assert not aq.get_state(States.POOL)
        assert aq.get_state(States.FILTER)
        assert aq.get_state(States.SPA)
