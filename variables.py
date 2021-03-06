#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jun 23 10:17:17 2021

@author: jonasg
"""
import os, shutil, glob

ALL_EBAS_VARS = ['concno2',
                 'concso2',
                 'concco',
                 'vmrc2h6',
                 'vmrc2h4',
                 'concpm25',
                 'concpm10',
                 'vmro3max',  # NB: EBAS variable is vmro3, but it is called vmro3max after resampled to daily max
                 'concso4',
                 'concNtno3',
                 'concNtnh',
                 'concNnh3',
                 'concNnh4',
                 'concNhno3',
                 'concNno3pm25',
                 'concNno3pm10',
                 'concsspm25',
                 'concss',
                 'concCecpm25',
                 'concCocpm25',
                 'conchcho',
                 'wetoxs',
                 'wetrdn',
                 'wetoxn',
                 'pr',
                 'vmrisop',
                 'concglyoxal'
                 ]
