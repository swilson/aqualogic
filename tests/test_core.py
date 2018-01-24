# -*- coding: utf-8 -*-

from .context import aqualogic
from io import FileIO
import pytest

def test_basic():
    stream = FileIO('tests/data/idle.bin')
    aq = aqualogic.AquaLogic(stream)
    aq.data_reader()
    assert aq.air_temp == 1
    assert aq.pool_temp == 0
    assert aq.chlorinator == 0
