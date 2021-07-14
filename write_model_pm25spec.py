# Calculate daily time series at stations from EMEP model grid output
import sys
import os

import pandas as pd

from read_mods import read_model, EMEP_VAR_UNITS, CALCULATE_HOW, get_modelfile
from helper_functions import clear_output

# Provide the range of years to include in the time series (both FIRST_YEAR and LAST_YEAR are included)
FIRST_YR = 2010
LAST_YR = 2019
#FIRST_YR = 2018  # !!!!!!!!!!!! for testing
#LAST_YR = 2019  # !!!!!!!!!!!! for testing

EBAS_VARS = [
             'concpm25',
             'concso4',
             'concnh4',
             'concno3pm25',
             'concCecpm25',
             'concoaf',
             'concCocpm25'
            ]

PFOLDER_DATA_REPOS = '../'
#PFOLDER_DATA_REPOS = '/home/eivindgw/testdata/'  # !!!!!!!!!!!!!! for testing

# Location and column specifications for the input file with station metadata
FILE_INDATA = 'input_data/sites_organics_trends_2010-2019.dat'
INDATA_COLSPECS = [(0, 7), (8, 48), (49, 59), (60, 71), (72, 79)]

DATA_FREQ = 'day'
#DATA_FREQ = 'month'  # !!!!!!!!!!!!!!!! for testing

DATA_FREQ_IN_FILENAME = {'day': 'daily', 'month': 'monthly', 'year': 'yearly'}

if __name__ == '__main__':

    data_freq_filestr = DATA_FREQ_IN_FILENAME[DATA_FREQ]

    # Verify that data repository exists
    DATAREPO_DIR = os.path.join(PFOLDER_DATA_REPOS, 'emep_trends_2021_data')
    if not os.path.exists(DATAREPO_DIR):
        raise IOError('Data repository folder "%s" does not exist' % DATAREPO_DIR)
    # Create pm25 speciation output folder
    PM25SPEC_MOD_OUTPUT_DIR = os.path.join(DATAREPO_DIR, 'mod_pm25spec')
    if not os.path.exists(PM25SPEC_MOD_OUTPUT_DIR):
        os.mkdir(PM25SPEC_MOD_OUTPUT_DIR)

    # Clear previous output (clear only output at the selected time resolution)
    clear_output(PM25SPEC_MOD_OUTPUT_DIR, f'pm25spec_*{data_freq_filestr}')

    # Read station metadata file
    indata = pd.read_fwf(FILE_INDATA, colspecs=INDATA_COLSPECS)
    indata = indata[~indata['Code'].str.contains('--')]  # remove ---- row
    indata['longitude'] = pd.to_numeric(indata['longitude'])
    indata['latitude'] = pd.to_numeric(indata['latitude'])
    indata.reset_index(drop=True, inplace=True)
    nst = len(indata)

    # Create station metadata lists to be used by to_time_series
    longitudes = list(indata['longitude'].values)
    latitudes = list(indata['latitude'].values)
    names = [indata['Station name'][i] for i in range(nst)]
    site_ids = [indata['Code'][i] for i in range(nst)]
    add_meta = {'station_id': site_ids, 'station_name': names}

    # Read data at each station location
    sitedata = dict([(site_ids[i], {}) for i in range(nst)])
    for var in EBAS_VARS:
        var_info = {var: {'units': EMEP_VAR_UNITS[var], 'data_freq': DATA_FREQ}}
        vardata = read_model(var, get_modelfile, FIRST_YR, LAST_YR+1, var_info, CALCULATE_HOW)
        stationdata_list = vardata.to_time_series(longitude=longitudes, latitude=latitudes, add_meta=add_meta)
        for sd in stationdata_list:
            site_id = sd.station_id
            sitedata[site_id][var] = sd[var]

    # Save data to one file per station
    for site_id in site_ids:
        moddf = pd.DataFrame.from_dict(sitedata[site_id], orient='columns')
        fname = f'pm25spec_ugm3_{site_id}_{FIRST_YR}-{LAST_YR}_{data_freq_filestr}.csv'
        modout = os.path.join(PM25SPEC_MOD_OUTPUT_DIR, fname)
        moddf.to_csv(modout)

    print('Done.')
