#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Calculate trends for precipitation
"""
import os, tqdm

import numpy as np
import pandas as pd
import pyaerocom as pya

from read_mods import read_model, get_modelfile
from helper_functions import clear_output, delete_outdated_output, get_years_to_read
from constants import PERIODS, EBAS_ID, EBAS_LOCAL, SEASONS
from variables import ALL_EBAS_VARS

RESAMPLE_HOW = 'sum'

RESAMPLE_CONSTRAINTS = dict(monthly= dict(daily=21),
                            daily=   dict(hourly=18))

EBAS_BASE_FILTERS = dict(set_flags_nan   = True,
                         #data_level      = 2
                         framework       = ['*EMEP*', '*ACTRIS*'])

VAR = 'pr'

PFOLDER_DATA_REPOS = '../'
#PFOLDER_DATA_REPOS = '/home/eivindgw/testdata/'  # !!!!!!!!!!!!!! for testing

if __name__ == '__main__':

    # Define output directories
    DATAREPO_DIR = os.path.join(PFOLDER_DATA_REPOS, 'emep_trends_2021_data')
    if not os.path.exists(DATAREPO_DIR):
        raise IOError('Data repository folder "%s" does not exist' % DATAREPO_DIR)

    OBS_OUTPUT_DIR = os.path.join(DATAREPO_DIR, 'obs_output')
    MODEL_OUTPUT_DIR = os.path.join(DATAREPO_DIR, 'mod_output')

    if not os.path.exists(OBS_OUTPUT_DIR):
        os.mkdir(OBS_OUTPUT_DIR)
    if not os.path.exists(MODEL_OUTPUT_DIR):
        os.mkdir(MODEL_OUTPUT_DIR)

    if os.path.exists(EBAS_LOCAL):
        data_dir = EBAS_LOCAL
    else:
        # try use lustre...
        data_dir = None

    # clear outdated output variables
    delete_outdated_output(OBS_OUTPUT_DIR, ALL_EBAS_VARS)
    delete_outdated_output(MODEL_OUTPUT_DIR, ALL_EBAS_VARS)

    start_yr, stop_yr = get_years_to_read(PERIODS)
    #start_yr = '2017'; stop_yr = '2018'  #!!!!!!!!!! for testing
    print(start_yr, stop_yr)

    oreader = pya.io.ReadUngridded(EBAS_ID, data_dirs=data_dir)

    if VAR not in ALL_EBAS_VARS:
        raise ValueError('invalid variable ', VAR, '. Please register'
                         'in variables.py')

    # delete previous output
    clear_output(OBS_OUTPUT_DIR, VAR)
    clear_output(MODEL_OUTPUT_DIR, VAR)
    sitemeta = []
    obs_trendtab = []
    mod_trendtab = []

    # Read observed precipitation
    data = oreader.read(vars_to_retrieve=VAR)
    data = data.apply_filters(**EBAS_BASE_FILTERS)

    # Read precipitation from daily model output
    var_info = {VAR: {'units': 'mm', 'data_freq': 'day'}}
    mdata = read_model(VAR, get_modelfile, start_yr, stop_yr, var_info)

    # Colocate model and observations at monthly resolution
    # (for now, do not colocated at each time before resampling)
    tst = 'monthly'
    coldata = pya.colocation.colocate_gridded_ungridded(
                mdata, data, ts_type=tst, start=start_yr, stop=stop_yr,
                colocate_time=False, resample_how=RESAMPLE_HOW,
                harmonise_units=False,
                min_num_obs=RESAMPLE_CONSTRAINTS
                )

    # Loop over stations in colcated data
    sitelist = list(coldata.data.station_name.values)
    for site in tqdm.tqdm(sitelist, desc=VAR):

        # Pick out monthly precipitation time series at this station
        obs_site = coldata.data.sel(station_name=site).isel(data_source=0).to_series()
        mod_site = coldata.data.sel(station_name=site).isel(data_source=1).to_series()
        # invalidate model at months with no observed monthly mean
        noobs = np.isnan(obs_site.values)
        mod_site = mod_site.where(~noobs, other=np.nan)
        obs_ts = obs_site.loc[start_yr:stop_yr]
        mod_ts = mod_site.loc[start_yr:stop_yr]
        if len(obs_ts) == 0 or np.isnan(obs_ts).all(): # skip
            continue

        # Read metadata
        sitedata_for_meta = data.to_station_data(
            site, VAR, start=int(start_yr), stop=int(stop_yr)+1,
            resample_how=RESAMPLE_HOW,
            min_num_obs=RESAMPLE_CONSTRAINTS
        )
        site_id = sitedata_for_meta.station_id
        # set unit to mm month-1 since this is the result of the summing in the colocated data
        coldata_unit = 'mm month-1'
        sitemeta.append([VAR,
                         site_id,
                         sitedata_for_meta.station_name,
                         sitedata_for_meta.latitude,
                         sitedata_for_meta.longitude,
                         sitedata_for_meta.altitude,
                         coldata_unit,
                         tst,
                         sitedata_for_meta.framework,
                         sitedata_for_meta.var_info[VAR]['matrix']
                         ])

        # Save monthly time series to files
        obs_subdir = os.path.join(OBS_OUTPUT_DIR, f'data_{VAR}')
        mod_subdir = os.path.join(MODEL_OUTPUT_DIR, f'data_{VAR}')
        os.makedirs(obs_subdir, exist_ok=True)
        os.makedirs(mod_subdir, exist_ok=True)

        fname = f'data_{VAR}_{site_id}_{tst}.csv'

        obs_siteout = os.path.join(obs_subdir, fname)
        obs_ts.to_csv(obs_siteout)

        mod_siteout = os.path.join(mod_subdir, fname)
        mod_ts.to_csv(mod_siteout)

        # Calculate trends at this station

        te = pya.trends_engine.TrendsEngine

        for (start, stop, min_yrs) in PERIODS:
            for seas in SEASONS:
                obs_trend = te.compute_trend(obs_ts, tst, start, stop, min_yrs,
                                             seas)

                obs_row = [VAR, site_id, obs_trend['period'], obs_trend['season'],
                           obs_trend[f'slp_{start}'], obs_trend[f'slp_{start}_err'],
                           obs_trend[f'reg0_{start}'], obs_trend['m'], obs_trend['m_err'],
                           obs_trend['n'], obs_trend['pval'], coldata_unit]

                obs_trendtab.append(obs_row)

                mod_trend = te.compute_trend(mod_ts, tst, start, stop, min_yrs,
                                             seas)

                mod_row = [VAR, site_id, mod_trend['period'], mod_trend['season'],
                           mod_trend[f'slp_{start}'], mod_trend[f'slp_{start}_err'],
                           mod_trend[f'reg0_{start}'], mod_trend['m'], mod_trend['m_err'],
                           mod_trend['n'], mod_trend['pval'], coldata_unit]

                mod_trendtab.append(mod_row)

                fname = f'{VAR}_{site_id}_{start}-{stop}_{seas}_yearly.csv'
                try:
                    obs_trend['data'].to_csv(os.path.join(obs_subdir, fname))
                    mod_trend['data'].to_csv(os.path.join(mod_subdir, fname))
                except AttributeError:
                    pass

    # Save sitemeta and trend results

    metadf = pd.DataFrame(sitemeta,
                          columns=['var',
                                   'station_id',
                                   'station_name',
                                   'latitude',
                                   'longitude',
                                   'altitude',
                                   'unit',
                                   'freq',
                                   'framework',
                                   'matrix'
                                   ])

    metaout = os.path.join(OBS_OUTPUT_DIR, f'sitemeta_{VAR}.csv')

    metadf.to_csv(metaout)

    obs_trenddf = pd.DataFrame(obs_trendtab,
                               columns=['var',
                                        'station_id',
                                        'period',
                                        'season',
                                        'trend [%/yr]',
                                        'trend err [%/yr]',
                                        'yoffs',
                                        'slope',
                                        'slope err',
                                        'num yrs',
                                        'pval',
                                        'unit'
                                        ])

    mod_trenddf = pd.DataFrame(mod_trendtab,
                               columns=['var',
                                        'station_id',
                                        'period',
                                        'season',
                                        'trend [%/yr]',
                                        'trend err [%/yr]',
                                        'yoffs',
                                        'slope',
                                        'slope err',
                                        'num yrs',
                                        'pval',
                                        'unit'
                                        ])

    obs_trendout = os.path.join(OBS_OUTPUT_DIR, f'trends_{VAR}.csv')
    obs_trenddf.to_csv(obs_trendout)

    mod_trendout = os.path.join(MODEL_OUTPUT_DIR, f'trends_{VAR}.csv')
    mod_trenddf.to_csv(mod_trendout)
    print(f'Processing of precipitation ({VAR}) is done.')
