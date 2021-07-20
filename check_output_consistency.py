"""
Script to check consistency of the processed files created by calc_trends.py,
calc_trends_o3.py and calc_trends_pr.py.
For each  component, it checks if trend output files and data files contain
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


def _print_set_diff(set1, set2):
    set1only = set1.difference(set2)
    set2only = set2.difference(set1)
    print('Only in first:', set1only)
    print('Only in second:', set2only)
    return


def check_consistency(var_name, data_repo_folder):
    """
    Do some simple checks that output is consistent
    """

    print('\n  %s' % var_name)

    lenvn = len(var_name)
    sitemeta_file = os.path.join(data_repo_folder, 'obs_output', 'sitemeta_%s.csv' % var_name)

    df = pd.read_csv(sitemeta_file, sep=',')
    station_ids_sitemeta = set(df['station_id'].values)
    nst = len(station_ids_sitemeta)

    print('\nFound %d stations in %s:' % (nst, sitemeta_file))
    #print(station_ids_sitemeta)

    # Check for specific stations in sitemeta
    # underlined in e-mail from Wenche
    """#station_pres = ['AT0005', 'CH0001', 'CH0005', 'DK0008', 'NO0002R;NO0001R', 'NO0039', 'NO0042', 'SK0002']
    # Not underlined
    station_pres = ['AT0048', 'DE0001', 'DE0003', 'DK0005', 'FI0036', 'IE0001']
    for sstring in station_pres:
        print('Searching for "%s"' % sstring)
        for sid in list(station_ids_sitemeta):
            if sid.startswith(sstring):
                print('  Found it in sitemeta as "%s"' % sid)
    sys.exit(0)"""

    # Check that the same stations are in trends and data files as in sitemeta
    print('Checking that stations appearing in sitemeta are the same as appearing elsewhere...')
    for subf in ['obs_output', 'mod_output']:
        # read trends file
        trends_file = os.path.join(data_repo_folder, subf, 'trends_%s.csv' % var_name)
        df_trend = pd.read_csv(trends_file, sep=',')
        # Find monthly data files
        if var_name == 'vmro3max':
            sstr_dayfiles = os.path.join(data_repo_folder, subf, 'data_%s/data_%s_*_daily.csv' % (var_name, var_name))
            dayfiles = glob.glob(sstr_dayfiles)
            ind0 = lenvn + 6
            ind1 = -10
            station_ids_day = set([os.path.basename(fn)[ind0:ind1] for fn in dayfiles])
            if station_ids_sitemeta != station_ids_day:
                print('Daily files in %s not the same as in sitemeta' % subf)
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
                    if station_ids_sitemeta != station_ids_trenddat:
                        print('Trend data files in %s for period %04d-%04d, percentile %d not the same as sitemeta' % (subf, y0, y1, perc))
                        _print_set_diff(station_ids_trenddat, station_ids_sitemeta)
                    # Find the trends of this data
                    cur_dft = df_trend.loc[(df_trend['percentile'] == perc) & (df_trend['period'] == per_str)]
                    station_ids_trendsf = set(cur_dft['station_id'].values)
                    if station_ids_sitemeta != station_ids_trendsf:
                        print('Trends file in %s does not include the same stations as sitemeta for period %04d-%04d, percentile %d' % (subf, y0, y1, perc))
                        _print_set_diff(station_ids_trendsf, station_ids_sitemeta)
        else:
            sstr_monthfiles = os.path.join(data_repo_folder, subf, 'data_%s/data_%s_*_monthly.csv' % (var_name, var_name))
            monthly_files = glob.glob(sstr_monthfiles)
            ind0 = lenvn + 6
            ind1 = -12
            station_ids_month = set([os.path.basename(fn)[ind0:ind1] for fn in monthly_files])
            #print('\nMonthly files in %s:' % subf)
            #print(station_ids_month)
            if station_ids_sitemeta != station_ids_month:
                print('Monthly files in %s not the same as in sitemeta' % subf)
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
                    if station_ids_sitemeta != station_ids_trenddat:
                        print('Trend data files in %s for period %04d-%04d, season %s not the same as sitemeta' % (subf, y0, y1, season))
                        _print_set_diff(station_ids_trenddat, station_ids_sitemeta)
                    # Find the trends of this data
                    cur_dft = df_trend.loc[(df_trend['season'] == season) & (df_trend['period'] == per_str)]
                    station_ids_trendsf = set(cur_dft['station_id'].values)
                    if station_ids_sitemeta != station_ids_trendsf:
                        print('Trends file in %s does not include the same stations as sitemeta for period %04d-%04d, season %s' % (subf, y0, y1, season))
                        _print_set_diff(station_ids_trendsf, station_ids_sitemeta)
    print('All data output locations checked')

    if var_name == 'vmro3max':
        print('Checking that days with data are the same in observations and model...')
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
                    #pd.set_option('display.max_rows', 1000)
                    #print(df[:])
        print('Done checking mod-vs-obs consistency')
    else:
        print('Checking that months with data are the same in observations and model...')
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
                    #pd.set_option('display.max_rows', 1000)
                    #print(df[:])
        print('Done checking mod-vs-obs consistency')
    return


if __name__ == '__main__':
    data_repo = '/home/eivindgw/code_work/emep_trends/emep_trends_2021_data'
    #data_repo = '/home/eivindgw/code_work/emep_trends/tmp_oldso2'
    #data_repo = '/home/eivindgw/testdata/emep_trends_2021_data'
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
        check_consistency(var, data_repo)
    print('Done.')
