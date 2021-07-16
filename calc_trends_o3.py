#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Module for processing percentiles of daily max ozone in model and observations
"""
import os, tqdm
import numpy as np
import pandas as pd
import pyaerocom as pya

from read_mods import read_model, get_modelfile, EMEP_VAR_UNITS
from helper_functions import (clear_output, delete_outdated_output,
                              get_years_to_read)
from constants import PERIODS, EBAS_ID, EBAS_LOCAL
from variables import ALL_EBAS_VARS

# email with Sverre and David on 22 June 2021
DEFAULT_RESAMPLE_CONSTRAINTS = dict(yearly     =   dict(daily      = 330),
                                    daily      =   dict(hourly     = 18))

# daily to yearly will be added below for each percentile
RESAMPLE_HOW = dict(daily=dict(hourly='max'))

# O3 percentiles for daily -> yearly
PERECENTILES = [10, 50, 75, 95, 98, 99]


def get_rs_how(percentile):
    """
    Get resampling dict for ozone for a given yearly percentile of daily max

    Parameters
    ----------
    percentile : int
        integer percentile to be used for daily -> yearly

    Returns
    -------
    dict
        resample_how dictionary
    """
    rs_how = {**RESAMPLE_HOW}
    rs_how['yearly'] = dict(daily=f'{percentile}percentile')
    return rs_how


# variable name in EBAS for original hourly ozone
VAR_ORIG = 'vmro3'
# variable name used in output files and in model data, for daily max ozone
VAR_DMAX = 'vmro3max'

# QC filters for EBAS data
EBAS_BASE_FILTERS = dict(set_flags_nan   = True,
                         #data_level      = 2,
                         framework       = ['*EMEP*', '*ACTRIS*'],
                         ts_type         = 'hourly')


# Folder where data repos are located. In this folder, there must already be located folders named
# 'emep_trends_2021_data' and 'emep_trends_2021_data_relaxed'.
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

    if VAR_DMAX not in ALL_EBAS_VARS:
        raise ValueError('invalid variable ', VAR_DMAX, '. Please register'
                         'in variables.py')

    # delete previous output
    clear_output(OBS_OUTPUT_DIR, VAR_DMAX)
    clear_output(MODEL_OUTPUT_DIR, VAR_DMAX)
    sitemeta = []
    obs_trendtab = []
    mod_trendtab = []

    data = oreader.read(vars_to_retrieve=VAR_ORIG)
    data = data.apply_filters(**EBAS_BASE_FILTERS)
    # data = data.apply_filters(station_id='GB0013R')

    # Read daily max ozone
    var_info = {VAR_DMAX: {'units': EMEP_VAR_UNITS[VAR_DMAX], 'data_freq': 'day'}}
    mdata = read_model(VAR_DMAX, get_modelfile, start_yr, stop_yr, var_info)

    tst = 'daily'

    coldata = pya.colocation.colocate_gridded_ungridded(
                mdata, data, ts_type=tst, start=start_yr, stop=stop_yr,
                var_ref=VAR_ORIG, colocate_time=True, resample_how=RESAMPLE_HOW,
                min_num_obs=DEFAULT_RESAMPLE_CONSTRAINTS
                )

    # Loop over stations in colocated data
    sitelist = list(coldata.data.station_name.values)
    for site in tqdm.tqdm(sitelist, desc=VAR_DMAX):

        # Pick out daily time series from observations and model at this station
        obs_data = coldata.data.sel(station_name=site).isel(data_source=0).to_series()
        mod_data = coldata.data.sel(station_name=site).isel(data_source=1).to_series()

        obs_ts = obs_data.loc[start_yr:stop_yr]
        mod_ts = mod_data.loc[start_yr:stop_yr]
        if len(obs_ts) == 0 or np.isnan(obs_ts).all():  # skip
            continue

        # Read metadata
        sitedata_for_meta = data.to_station_data(
            site, VAR_ORIG, start=int(start_yr), stop=int(stop_yr)+1,
            resample_how=RESAMPLE_HOW,
            min_num_obs=DEFAULT_RESAMPLE_CONSTRAINTS
        )
        site_id = sitedata_for_meta.station_id

        unit = sitedata_for_meta.get_unit(VAR_ORIG)
        sitemeta.append([VAR_DMAX,
                         site_id,
                         sitedata_for_meta.station_name,
                         sitedata_for_meta.latitude,
                         sitedata_for_meta.longitude,
                         sitedata_for_meta.altitude,
                         unit,
                         tst,
                         sitedata_for_meta.framework,
                         sitedata_for_meta.var_info[VAR_ORIG]['matrix']
                         ])

        # Save daily time series to files
        obs_subdir = os.path.join(OBS_OUTPUT_DIR, f'data_{VAR_DMAX}')
        mod_subdir = os.path.join(MODEL_OUTPUT_DIR, f'data_{VAR_DMAX}')
        os.makedirs(obs_subdir, exist_ok=True)
        os.makedirs(mod_subdir, exist_ok=True)

        fname = f'{VAR_DMAX}_{site_id}_{tst}.csv'

        obs_siteout = os.path.join(obs_subdir, fname)
        obs_ts.to_csv(obs_siteout)

        mod_siteout = os.path.join(mod_subdir, fname)
        mod_ts.to_csv(mod_siteout)

        # Create stationdata objects with the time series
        varinfo = {VAR_DMAX: {'ts_type': tst}}
        obs_site = pya.StationData(var_info=varinfo)
        obs_site[VAR_DMAX] = obs_data
        mod_site = pya.StationData(var_info=varinfo)
        mod_site[VAR_DMAX] = mod_data

        # Go through all percentiles and create trend analysis
        tst_trend = 'yearly'
        for percentile in PERECENTILES:
            rs_how = get_rs_how(percentile)
            try:
                obs_site_trend = obs_site.resample_time(
                    var_name=VAR_DMAX,
                    ts_type=tst_trend,
                    min_num_obs=DEFAULT_RESAMPLE_CONSTRAINTS,
                    how=rs_how, inplace=False)
                mod_site_trend = mod_site.resample_time(
                    var_name=VAR_DMAX,
                    ts_type=tst_trend,
                    min_num_obs=DEFAULT_RESAMPLE_CONSTRAINTS,
                    how=rs_how, inplace=False)
            except pya.exceptions.TemporalResolutionError:
                continue  # lower res than daily ?????????????????????

            obs_ts_perc = obs_site_trend[VAR_DMAX]
            mod_ts_perc = mod_site_trend[VAR_DMAX]
            if len(obs_ts_perc) == 0 or np.isnan(obs_ts_perc).all():  # skip
                continue

            te = pya.trends_engine.TrendsEngine

            for (start, stop, min_yrs) in PERIODS:

                obs_trend = te.compute_trend(
                    obs_ts_perc, tst_trend, start, stop, min_yrs, 'all')

                obs_row = [
                    VAR_DMAX, site_id, obs_trend['period'], obs_trend['season'],
                    obs_trend[f'slp_{start}'], obs_trend[f'slp_{start}_err'],
                    obs_trend[f'reg0_{start}'], obs_trend['m'], obs_trend['m_err'],
                    obs_trend['n'], obs_trend['pval'], unit, percentile]

                obs_trendtab.append(obs_row)

                mod_trend = te.compute_trend(
                    mod_ts_perc, tst_trend, start, stop, min_yrs, 'all')

                mod_row = [
                    VAR_DMAX, site_id, mod_trend['period'], mod_trend['season'],
                    mod_trend[f'slp_{start}'], mod_trend[f'slp_{start}_err'],
                    mod_trend[f'reg0_{start}'], mod_trend['m'], mod_trend['m_err'],
                    mod_trend['n'], mod_trend['pval'], unit, percentile]

                mod_trendtab.append(mod_row)

                fname = f'{VAR_DMAX}_{site_id}_{start}-{stop}_{percentile}p_yearly.csv'
                try:
                    obs_trend['data'].to_csv(os.path.join(obs_subdir, fname))
                    mod_trend['data'].to_csv(os.path.join(mod_subdir, fname))
                except AttributeError:
                    pass

    # Save sitemeta and trend results

    metadf = pd.DataFrame(
        sitemeta,
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

    metaout = os.path.join(OBS_OUTPUT_DIR, f'sitemeta_{VAR_DMAX}.csv')

    metadf.to_csv(metaout)

    obs_trenddf = pd.DataFrame(
        obs_trendtab,
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
                 'unit',
                 'percentile'
                 ])

    mod_trenddf = pd.DataFrame(
        mod_trendtab,
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
                 'unit',
                 'percentile'
                 ])

    obs_trendout = os.path.join(OBS_OUTPUT_DIR, f'trends_{VAR_DMAX}.csv')
    obs_trenddf.to_csv(obs_trendout)

    mod_trendout = os.path.join(MODEL_OUTPUT_DIR, f'trends_{VAR_DMAX}.csv')
    mod_trenddf.to_csv(mod_trendout)
    print('Processing of ozone done.')
