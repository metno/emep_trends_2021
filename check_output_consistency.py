"""
Script to check consistency of the processed files created by calc_trends.py,
calc_trends_o3.py and calc_trends_pr.py.
For each component, it checks if trend output files and data files contain
the same stations as in sitemeta, and if observations and model exist in
the same months in the monthly time series.
"""
import os
import sys
import glob

import numpy as np
import pandas as pd

from calc_trends import PERIODS
from calc_trends_o3 import PERECENTILES
from constants import SEASONS


def check_consistency(var_name, data_repo_folder):
    """
    Do simple checks that output created by calc_trends scripts is consistent

    Any inconsistencied discovered will be printed.

    NB: Not all inconsistencies mean that something is wrong. If not all
    stations that exist in sitemeta are found in the trends file or trends
    time series, it could be because they have too little data coverage.
    However, if model and observations are not NaN at the same times, it is
    a bug.

    Parameters
    ----------
    var_name : string
        The pyaerocom variable name to check
    data_repo_folder : string
        Path to the repository where the output to check has been saved
        (either the usual data repo or the relaxed data repo)
    """
    lenvn = len(var_name)

    # Check which stations exist in the sitemeta file
    sitemeta_file = os.path.join(data_repo_folder, 'obs_output', 'sitemeta_%s.csv' % var_name)
    df = pd.read_csv(sitemeta_file, sep=',')
    station_ids_sitemeta = set(df['station_id'].values)
    nst = len(station_ids_sitemeta)

    print('\nFound %d stations in %s' % (nst, sitemeta_file))

    # Check that the same stations are in trends and data files as in sitemeta
    for subf in ['obs_output', 'mod_output']:
        # read trends file
        trends_file = os.path.join(data_repo_folder, subf, 'trends_%s.csv' % var_name)
        df_trend = pd.read_csv(trends_file, sep=',')
        if var_name == 'vmro3max':
            # Find daily files for ozone
            sstr_dayfiles = os.path.join(data_repo_folder, subf, 'data_%s/data_%s_*_daily.csv' % (var_name, var_name))
            dayfiles = glob.glob(sstr_dayfiles)
            ind0 = lenvn + 6
            ind1 = -10
            station_ids_day = set([os.path.basename(fn)[ind0:ind1] for fn in dayfiles])
            if station_ids_day != station_ids_sitemeta:
                print('Daily files in %s does not have the same stations as in sitemeta' % subf)
                _print_set_diff(station_ids_day, station_ids_sitemeta)
            # For each period and percentile, find trends data files and trends
            for per in PERIODS:
                y0 = per[0]
                y1 = per[1]
                per_str = '%04d-%04d' % (y0, y1)
                for perc in PERECENTILES:
                    sstr_perc = os.path.join(data_repo_folder, subf, 'data_%s/%s_*_%04d-%04d_%02dp_yearly.csv' % (var_name, var_name, y0, y1, perc))
                    trend_files = glob.glob(sstr_perc)
                    ind0 = lenvn + 1
                    ind1 = -25
                    station_ids_trenddat = set([os.path.basename(fn)[ind0:ind1] for fn in trend_files])
                    if station_ids_trenddat != station_ids_sitemeta:
                        print('Trend time series files in %s for period %04d-%04d, percentile %d, does not have the same stations as sitemeta' % (subf, y0, y1, perc))
                        _print_set_diff(station_ids_trenddat, station_ids_sitemeta)
                    # Find the trends of this data
                    cur_dft = df_trend.loc[(df_trend['percentile'] == perc) & (df_trend['period'] == per_str)]
                    station_ids_trendsf = set(cur_dft['station_id'].values)
                    if station_ids_trendsf != station_ids_trenddat:
                        print('Trends file in %s does not include the same stations as the trend time series for period %04d-%04d, percentile %d' % (subf, y0, y1, perc))
                        _print_set_diff(station_ids_trendsf, station_ids_trenddat)
        else:
            # Find monthly data files
            sstr_monthfiles = os.path.join(data_repo_folder, subf, 'data_%s/data_%s_*_monthly.csv' % (var_name, var_name))
            monthly_files = glob.glob(sstr_monthfiles)
            ind0 = lenvn + 6
            ind1 = -12
            station_ids_month = set([os.path.basename(fn)[ind0:ind1] for fn in monthly_files])
            if station_ids_month != station_ids_sitemeta:
                print('Monthly files in %s does not have the same stations as in sitemeta' % subf)
                _print_set_diff(station_ids_month, station_ids_sitemeta)
            # For each period and season, find trends data files and trends
            for per in PERIODS:
                y0 = per[0]
                y1 = per[1]
                per_str = '%04d-%04d' % (y0, y1)
                for season in SEASONS:
                    sstr_season = os.path.join(data_repo_folder, subf, 'data_%s/%s_*_%04d-%04d_%s_yearly.csv' % (var_name, var_name, y0, y1, season))
                    trend_files = glob.glob(sstr_season)
                    ind0 = lenvn + 1
                    ind1 = -len(season) - 22
                    station_ids_trenddat = set([os.path.basename(fn)[ind0:ind1] for fn in trend_files])
                    if station_ids_trenddat != station_ids_sitemeta:
                        print('Trend time series files in %s for period %04d-%04d, season %s, does not have the same stations as sitemeta' % (subf, y0, y1, season))
                        _print_set_diff(station_ids_trenddat, station_ids_sitemeta)
                    # Find the trends of this data
                    cur_dft = df_trend.loc[(df_trend['season'] == season) & (df_trend['period'] == per_str)]
                    station_ids_trendsf = set(cur_dft['station_id'].values)
                    if station_ids_trendsf != station_ids_trenddat:
                        print('Trends file in %s does not include the same stations as the trend time series for period %04d-%04d, season %s' % (subf, y0, y1, season))
                        _print_set_diff(station_ids_trendsf, station_ids_trenddat)

    if var_name == 'vmro3max':
        # Check if any stations have different days with data for model than observations
        for station_id in station_ids_sitemeta:
            dayfile_obs = os.path.join(data_repo_folder, 'obs_output', 'data_%s/%s_%s_daily.csv' % (var_name, var_name, station_id))
            dayfile_mod = os.path.join(data_repo_folder, 'mod_output', 'data_%s/%s_%s_daily.csv' % (var_name, var_name, station_id))
            if os.path.exists(dayfile_obs) and os.path.exists(dayfile_mod):
                ser_obs = pd.read_csv(dayfile_obs, sep=',', index_col=0)[var_name]
                ser_mod = pd.read_csv(dayfile_mod, sep=',', index_col=0)[var_name]
                df = pd.DataFrame({'obs': ser_obs, 'mod': ser_mod})
                obsnan = np.isnan(df['obs'].values)
                modnan = np.isnan(df['mod'].values)
                if not np.all(obsnan == modnan):
                    nnan_obs = np.sum(obsnan)
                    nnan_mod = np.sum(modnan)
                    ntot = len(obsnan)
                    print('  - %s does not have NaNs in the same days in observations and model. In obs: %d/%d NaNs. In mod: %d/%d NaN' % (station_id, nnan_obs, ntot, nnan_mod, ntot))
    else:
        # Check if any stations have different months with data for model than observations
        for station_id in station_ids_sitemeta:
            monthfile_obs = os.path.join(data_repo_folder, 'obs_output', 'data_%s/data_%s_%s_monthly.csv' % (var_name, var_name, station_id))
            monthfile_mod = os.path.join(data_repo_folder, 'mod_output', 'data_%s/data_%s_%s_monthly.csv' % (var_name, var_name, station_id))
            if os.path.exists(monthfile_obs) and os.path.exists(monthfile_mod):
                ser_obs = pd.read_csv(monthfile_obs, sep=',', index_col=0)[var_name]
                ser_mod = pd.read_csv(monthfile_mod, sep=',', index_col=0)[var_name]
                df = pd.DataFrame({'obs': ser_obs, 'mod': ser_mod})
                obsnan = np.isnan(df['obs'].values)
                modnan = np.isnan(df['mod'].values)
                if not np.all(obsnan == modnan):
                    nnan_obs = np.sum(obsnan)
                    nnan_mod = np.sum(modnan)
                    ntot = len(obsnan)
                    print('  - %s does not have NaNs in the same months in observations and model. In obs: %d/%d NaNs. In mod: %d/%d NaN' % (station_id, nnan_obs, ntot, nnan_mod, ntot))
    return


def _print_set_diff(set1, set2):
    set1only = set1.difference(set2)
    set2only = set2.difference(set1)
    print('Only in first:', set1only)
    print('Only in second:', set2only)
    return


if __name__ == '__main__':
    data_repo = '/home/eivindgw/code_work/emep_trends/emep_trends_2021_data'
    #data_repo = '/home/eivindgw/code_work/emep_trends/emep_trends_2021_data_relaxed'
    variables = [
        'concno2',
        'concso2',
        'concco',
        'vmrc2h6',
        'vmrc2h4',
        'concpm25',
        'concpm10',
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
        'vmrisop',
        'concglyoxal',
        'vmro3max',
        'pr'
        ]
    for var in variables:
        print('\n  %s' % var)
        check_consistency(var, data_repo)
    print('Done.')
