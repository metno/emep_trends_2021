#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Common constants to use in all the scripts for trend calculations
"""
from pyaerocom.trends_helpers import SEASONS

SEASONS = ['all'] + list(SEASONS)

EBAS_LOCAL = '/home/jonasg/MyPyaerocom/data/obsdata/EBASMultiColumn/data'
EBAS_ID = 'EBASMC'

# Each tuple defines a period:
# - The first and second elements are the first and last year included in the period
# - The last element is the minimum number of years required for calculating a trend
PERIODS = [(2000, 2019, 14),
           (2000, 2010, 7),
           (2010, 2019, 7),
           (2005, 2019, 10)]
