#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jun 23 09:32:56 2021

@author: hansb
"""
import os, socket, tqdm
import iris
import cf_units
import pyaerocom as pya
import warnings

import derive_cubes as der

# Units that the variables from EMEP should have, when returned by read_mods
# (this may differ from the unit in the EMEP output file, since some unit
# transformation may be done in the calculate_how-step or in the final
# GriddedData initialization)
EMEP_VAR_UNITS = {
    'concno2': 'ug m-3',
    'concso2': 'ug m-3',
    'concco': 'ug m-3',
    'vmrc2h6': 'ppb',
    'vmrc2h4': 'ppb',
    'concpm25': 'ug m-3',
    'concpm10': 'ug m-3',
    'vmro3': 'ppb',
    'vmro3max': 'ppb',
    'concso4': 'ug m-3',
    'concNtno3': 'ug N m-3',
    'concNtnh': 'ug N m-3',
    'concNnh3': 'ug N m-3',
    'concNnh4': 'ug N m-3',
    'concNhno3': 'ug N m-3',
    'concNno3pm25': 'ug N m-3',
    'concNno3pm10': 'ug N m-3',
    'concsspm25': 'ug m-3',
    'concss': 'ug m-3',
    'concCecpm25': 'ug C m-3',
    'concCocpm25': 'ug C m-3',
    'conchcho': 'ug m-3',
    'wetoxs': 'mg S m-2 d-1',
    'wetrdn': 'mg N m-2 d-1',
    'wetoxn': 'mg N m-2 d-1',
    'vmrisop': 'ppb',
    'concglyoxal': 'ug m-3',
    # variables only used in pm25 speciation
    'concnh4': 'ug m-3',
    'concno3pm25': 'ug m-3',
    'concoaf': 'ug m-3'
}

CALCULATE_HOW = {
    'concNtnh': {'req_vars': ['concnh3', 'concnh4'],
                    'function': der.calc_concNtnh},
    'concco': {'req_vars': ['vmrco'],
                'function': der.conc_from_vmr_STP},
    'concNtno3': {'req_vars': ['conchno3', 'concno3f', 'concno3c'],
                    'function': der.calc_concNtno3},
    'concNnh3': {'req_vars': ['concnh3'],
                    'function': der.calc_concNnh3},
    'concNnh4': {'req_vars': ['concnh4'],
                    'function': der.calc_concNnh4},
    'concNhno3': {'req_vars': ['conchno3'],
                    'function': der.calc_concNhno3},
    'concNno3pm25': {'req_vars': ['concno3f', 'concno3c'],  # NB: fine before coarse!
                        'function': der.calc_concNno3pm25},
    'concNno3pm10': {'req_vars': ['concno3f', 'concno3c'],
                        'function': der.calc_concNno3pm10},
    'concno3pm25': {'req_vars': ['concno3f', 'concno3c'],
                    'function': der.calc_concno3pm25},
    'conchcho': {'req_vars': ['vmrhcho'],
                    'function': der.conc_from_vmr_STP},
    'concglyoxal': {'req_vars': ['vmrglyoxal'],
                    'function': der.conc_from_vmr_STP},
    'concCecpm25': {'req_vars': ['concCecpm25'],
                    'function': der.fix_ecunits}
}

HOSTNAME = socket.gethostname()

if HOSTNAME == 'pc5302':
    preface = '/home/hansb'
else:
    preface = '/'


def get_modelfile(year, data_freq):
    """
    Function to use as input argument 'getfile' in function read_model
    """
    folder = f'{preface}/lustre/storeB/project/fou/kl/emep/ModelRuns/2021_REPORTING/TRENDS/{year}'
    if data_freq not in ['hour', 'day', 'month']:
        raise ValueError('data_freq must be "hour", "day" or "month"')
    return os.path.join(folder, f'Base_{data_freq}.nc')


def dummy(cube):
    return cube


def not_implemented(cube):
    raise NotImplementedError


def read_model(var, getfile, start_yr, stop_yr, var_info, calc_how={}):
    """
    Read a model variable from multiple annual EMEP runs

    Parameters
    ----------
    var : string
        Variable name (in pyaerocom).
    getfile : function (int, str) -> str
        Function to get full path to the model data file for a specified year.
        First input argument should be the year and second should be the data
        time frequency, e.g. 'day', 'month', 'hour'
    start_yr : string or int
        Start year as sting or int.
    stop_yr : string or int
        Stop year as sting or int.
    var_info : dict
        Dict of dicts of variable metadata/info. Needs to have a key for var
        which has at least the keys "units" and "data_freq".
        It is verified that the final cube has units equivalent to "units",
        and "data_freq" is used as input to "getfile".
    calc_how : dict, optional
        If var is a variable that can not be read directly from the model data,
        calc_how should be provided. The dict must then contain an entry for the
        variable you want to process which must be another dict with keys "req_vars"
        and "function". "req_vars" must be a list of variable names and "function"
        must be a fuction that calculates the variable and returns an iris.cubc.Cube
        object. This returned cube object must have properties "var_name"=var and
        units equivalent to var_info[var]['units'].

    Returns
    -------
    concatenated : pyaerocom.GriddedData
        GriddedData object containing the requested variable covering the requested
        time period.
    """
    print(f'Reading {var} from model output')

    try:
        calculate_how = calc_how[var]
    except KeyError:
        calculate_how = {'req_vars': [var], 'function': dummy}

    data_freq = var_info[var]['data_freq']
    data = []

    years = range(int(start_yr), int(stop_yr))

    for year in tqdm.tqdm(years, desc=var):
        infile = getfile(year, data_freq)
        if not os.path.exists(infile):
            warnings.warn('No model data found for year %d. File %s not found' % (year, infile))
            continue

        reader = pya.io.ReadMscwCtm(infile)

        temp_data = []
        for req_var in calculate_how['req_vars']:
            temp = reader.read_var(req_var)
            tcoord = temp.cube.coords('time')[0]
            if tcoord.units.calendar == 'proleptic_gregorian':
                tcoord.units = cf_units.Unit(tcoord.units.origin, calendar='gregorian')
            temp_data.append(temp.cube)
        calc_temp = calculate_how['function'](*temp_data)
        data.append(calc_temp)

    concatenated = pya.GriddedData(pya.io.iris_io.concatenate_iris_cubes(iris.cube.CubeList(data), True))
    # verify final var_name and units
    assert concatenated.cube.var_name == var
    if concatenated.cube.units != var_info[var]['units']:
        error_str = ('Calculation of variable "%s" result in units "%s", not the expected units "%s"'
                     % (var, concatenated.cube.units, var_info[var]['units']))
        raise ValueError(error_str)

    return concatenated


if __name__ == '__main__':

    start_yr = 2019
    stop_yr = 2020

    var = 'pr'
    dfreq = 'month'

    var_info = {var: {'units': EMEP_VAR_UNITS[var], 'data_freq': dfreq}}
    mdata = read_model(var, get_modelfile, start_yr, stop_yr, var_info, CALCULATE_HOW)
    print(mdata)
