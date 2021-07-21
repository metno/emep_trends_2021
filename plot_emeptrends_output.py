"""
Module for plotting output created by the trends code
"""
import os
import datetime

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

from calc_trends_o3 import PERECENTILES


def plot_var(var, repo_folder):
    """
    Plot observed and modelled time series for each station of a variable

    The function will save a figure in png format to a subfolder "plot" in the
    indicated repo_folder. This figure will have one subplot per station that
    is defined in the sitemeta file of the indicated variable.
    If var='vmro3max' the subplots will show the yearly time series of each
    percentile of ozone. Otherwise, the monthly time series of 'var' will be
    shown.

    If there are more than 25 stations with the variable, the figure will be
    split over multiple png-files.

    Parameters
    ----------
    var : string
        A variable that has been processed, defined in variables.py
    repo_folder : string
        Path to the data repository
    """
    nmax = 25
    fontsize_lab = 14
    fontsize_leg_o3 = 10
    # Create folder for figure file
    figfolder = os.path.join(DATAREPO_DIR, 'plots')
    if not os.path.exists(figfolder):
        os.mkdir(figfolder)
    # Read station metadata
    sitemeta_file = os.path.join(repo_folder, 'obs_output', 'sitemeta_%s.csv' % var)
    df_meta = pd.read_csv(sitemeta_file)
    df_meta = df_meta.set_index('station_id')
    stations = list(df_meta.index)
    stations.sort()
    nst = len(stations)
    if nst == 0:
        print('No stations for %s' % var)
        return

    # Plot time series of model and observation at each station
    nfigs = int(np.ceil(nst/nmax))
    for j in range(nfigs):
        fnsuffix = '_part%02d' % (j+1) if nfigs > 1 else ''
        jstartidx = j*nmax
        jstopidx = min((j+1)*nmax, nst)
        jstations = stations[jstartidx:jstopidx]
        nstj = len(jstations)
        nrow = int(np.ceil(np.sqrt(nstj)))
        ncolm = int(np.ceil(nstj/nrow))
        fig = plt.figure(figsize=(7*ncolm, 5*nrow))
        if var == 'vmro3max':
            figfile = os.path.join(figfolder, '%s_%04d-%04d_yearly%s.png' % (var, O3_PERIOD[0], O3_PERIOD[1], fnsuffix))
        else:
            figfile = os.path.join(figfolder, 'data_%s_monthly%s.png' % (var, fnsuffix))
        for i in range(nstj):
            sid = jstations[i]
            iunits = df_meta['unit'][sid]
            if var == 'vmro3max':
                ax = plt.subplot(nrow, ncolm, i+1)
                for k, perc in enumerate(PERECENTILES[::-1]):
                    kcolor = LINE_COLORS[k]
                    basename = '%s_%s_%04d-%04d_%02dp_yearly.csv' % (var, sid, O3_PERIOD[0], O3_PERIOD[1], perc)
                    obsdata_file = os.path.join(repo_folder, 'obs_output', 'data_%s/%s' % (var, basename))
                    moddata_file = os.path.join(repo_folder, 'mod_output', 'data_%s/%s' % (var, basename))
                    if os.path.exists(obsdata_file):  # then moddata_file should also exist!
                        df_obs = pd.read_csv(obsdata_file, index_col=0)
                        df_mod = pd.read_csv(moddata_file, index_col=0)
                        df = pd.DataFrame({'obs': df_obs[var], 'mod': df_mod[var]})
                        times = df.index.astype('datetime64[ns]')
                        plt.plot(times, df['obs'].values, c=kcolor, ls='-', marker='x', markersize=3)
                        plt.plot(times, df['mod'].values, c=kcolor, ls='--', marker='.', markersize=3)
                        plt.plot([], [], c=kcolor, ls='-', label='%02dp' % perc)
                plt.plot([], [], c='k', ls='-', marker='x', markersize=3, label='obs')
                plt.plot([], [], c='k', ls='--', marker='.', markersize=3, label='model')
                datefmt = mdates.DateFormatter('%Y')
                plt.xlabel('Year', fontsize=fontsize_lab)
                plt.legend(loc=0, fontsize=fontsize_leg_o3)
                plt.title(sid)
                plt.ylabel('%s (%s)' % (var, iunits), fontsize=fontsize_lab)
                ax.xaxis.set_major_formatter(datefmt)
                plt.xticks(rotation=45)
            else:
                basename = 'data_%s_%s_monthly.csv' % (var, sid)
                obsdata_file = os.path.join(repo_folder, 'obs_output', 'data_%s/%s' % (var, basename))
                moddata_file = os.path.join(repo_folder, 'mod_output', 'data_%s/%s' % (var, basename))
                if os.path.exists(obsdata_file):  # then moddata_file should also exist!
                    ax = plt.subplot(nrow, ncolm, i+1)
                    df_obs = pd.read_csv(obsdata_file, index_col=0)
                    df_mod = pd.read_csv(moddata_file, index_col=0)
                    df = pd.DataFrame({'obs': df_obs[var], 'mod': df_mod[var]})
                    times = df.index.astype('datetime64[ns]')
                    datefmt = _create_datefmt(times)
                    xlab = 'Time UTC (%s)' % (_create_datelab(times[[0, -1]]))
                    plt.plot(times, df['obs'].values, c=LINE_COLORS[0], marker='.', markersize=2, label='obs')
                    plt.plot(times, df['mod'].values, c=LINE_COLORS[1], marker='.', markersize=2, label='model')
                    plt.xlabel(xlab, fontsize=fontsize_lab)
                    plt.legend(loc=0)
                    plt.title(sid)
                    plt.ylabel('%s (%s)' % (var, iunits), fontsize=fontsize_lab)
                    ax.xaxis.set_major_formatter(datefmt)
                    plt.xticks(rotation=45)
        fig.subplots_adjust(hspace=.7, wspace=.3)
        fig.savefig(figfile, bbox_inches='tight', dpi=200)
        plt.close(fig)
        print('Saved figure to %s' % figfile)
    return


def _create_datelab(period):
    "Create xlabel to be used in time series plot, from start and end of period"
    # Ensure period is in python datetime format
    t0 = period[0]
    t1 = period[1]
    if not isinstance(t0, datetime.datetime):
        t0 = pd.Timestamp(t0).to_pydatetime()
    if not isinstance(t1, datetime.datetime):
        t1 = pd.Timestamp(t1).to_pydatetime()
    if t0.month == t1.month and t0.year == t1.year:
        if t0.day == t1.day:
            lab = "%d/%d/%d" % (t0.day, t0.month, t0.year)
        else:
            lab = "%d-%d/%d/%d" % (t0.day, t1.day, t0.month, t0.year)
    else:
        lab = "%d/%d/%d-%d/%d/%d" % (
            t0.day, t0.month, t0.year, t1.day, t1.month, t1.year
            )
    return lab


def _create_datefmt(times):
    "Create the date tick format fitting the times"
    # Transform to python datetime type
    nt = len(times)
    times = np.array(times).astype('datetime64[s]')
    times = np.array(
        [datetime.datetime.utcfromtimestamp(times[i].astype(int))
         for i in range(nt)]
        )
    # Total number of seconds
    nsec_tot = (times[-1] - times[0]).total_seconds()
    # Determine what format we should have
    if nsec_tot > 3600*24*1000:
        datefmt = mdates.DateFormatter('%Y-%m')
    else:
        datefmt = mdates.DateFormatter('%Y-%m-%d')
    return datefmt


DATAREPO_DIR = os.path.join('../emep_trends_2021_data')
O3_PERIOD = (2000, 2019)
LINE_COLORS = [u'#1f77b4', u'#ff7f0e', u'#2ca02c', u'#d62728', u'#9467bd', u'#8c564b', u'#e377c2', u'#7f7f7f', u'#bcbd22', u'#17becf']

if __name__ == '__main__':
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
        'concglyoxal'
        'vmro3max'
        'pr'
    ]
    variables = ['concno2']

    for var in variables:
        print('var=', var)
        plot_var(var, DATAREPO_DIR)
    print('Done.')
