"""
Plot number of stations with obsdata as function of time for each variable
"""
import os
import warnings

import pandas as pd
import matplotlib.pyplot as plt

from plot_emeptrends_output import _create_datefmt, _create_datelab, LINE_COLORS


def plot_nstations_timeseries(varnames, repo_folder, ax=None):
    """
    Plot time series of number of stations with data. For now, not ozone
    """
    # Read all monthly time series and count number of stations in each month
    count_series = {}
    for var in varnames:
        sitemeta_file = os.path.join(repo_folder, 'obs_output', 'sitemeta_%s.csv' % var)
        if not os.path.exists(sitemeta_file):
            warnings.warn('No sitemeta file found for variable "%s". Skipping it.' % var)
            continue
        df_meta = pd.read_csv(sitemeta_file)
        df_meta = df_meta.set_index('station_id')
        stations = list(df_meta.index)
        stations.sort()
        nst = len(stations)
        if nst == 0:
            print('No stations for %s' % var)
            return
        station_series = {}
        for station in stations:
            basename = 'data_%s_%s_monthly.csv' % (var, station)
            obstsfile = os.path.join(repo_folder, 'obs_output', 'data_%s/%s' % (var, basename))
            if os.path.exists(obstsfile):  # then moddata_file should also exist!
                df_obs = pd.read_csv(obstsfile, index_col=0)
                station_series[station] = df_obs[var]
        if len(station_series) > 0:
            df_var = pd.DataFrame(station_series)
            count_series[var] = df_var.count(axis=1)
    if len(count_series) > 0:
        df_count = pd.DataFrame(count_series)
        _plot_count(df_count, ax)
    return


def plot_nstations_timeseries_vmro3max(repo_folder, ax=None):
    sitemeta_file = os.path.join(repo_folder, 'obs_output', 'sitemeta_vmro3max.csv')
    if not os.path.exists(sitemeta_file):
        warnings.warn('No sitemeta file found for variable "vmro3max"')
        return
    df_meta = pd.read_csv(sitemeta_file)
    df_meta = df_meta.set_index('station_id')
    stations = list(df_meta.index)
    stations.sort()
    nst = len(stations)
    if nst == 0:
        print('No stations for vmro3max')
        return
    station_series = {}
    for station in stations:
        basename = 'data_vmro3max_%s_daily.csv' % station
        obstsfile = os.path.join(repo_folder, 'obs_output', 'data_vmro3max', basename)
        if os.path.exists(obstsfile):  # then moddata_file should also exist!
            df_obs = pd.read_csv(obstsfile, index_col=0)
            station_series[station] = df_obs['vmro3max']
    if len(station_series) > 1:
        df_var = pd.DataFrame(station_series)
        count = df_var.count(axis=1)
        df_count = pd.DataFrame({'vmro3max': count})
        _plot_count(df_count, ax)
    return


def _plot_count(df, ax):
    if ax is None:
        ax = plt.gca()
    # Plot
    varnames = list(df.columns)
    times = df.index.astype('datetime64[ns]')
    datefmt = _create_datefmt(times)
    xlab = 'Time UTC (%s)' % (_create_datelab(times[[0, -1]]))
    plt.sca(ax)
    for i, var in enumerate(varnames):
        plt.plot(times, df[var].values, c=LINE_COLORS[i], label=var)
    plt.xlabel(xlab)
    plt.legend(loc=2)
    plt.ylabel('nr of stations')
    ax.xaxis.set_major_formatter(datefmt)
    plt.xticks(rotation=45)
    return ax


if __name__ == '__main__':
    # The variables to plot grouped together
    # NB: 8 groups are defined here. vmro3max is plotted as group 9
    plotgrps = [
        ['concno2', 'concso2', 'concco', 'concso4'],
        ['vmrc2h6', 'vmrc2h4', 'vmrisop', 'concglyoxal', 'conchcho'],
        ['concpm25', 'concpm10'],
        ['concNtno3', 'concNtnh', 'concNnh3', 'concNnh4'],
        ['concNhno3', 'concNno3pm25', 'concNno3pm10'],
        ['concsspm25', 'concss'],
        ['concCecpm25', 'concCocpm25'],
        ['wetoxs', 'wetrdn', 'wetoxn', 'pr']
    ]

    repo_folder = os.path.join('../emep_trends_2021_data')
    #repo_folder = os.path.join('../emep_trends_2021_data_relaxed')

    plot_folder = os.path.join(repo_folder, 'plots')
    if not os.path.exists(plot_folder):
        os.mkdir(plot_folder)
    figfile = os.path.join(plot_folder, 'stationcount.png')
    fig = plt.figure(figsize=(20, 15))
    for i, varnames in enumerate(plotgrps):
        ax = plt.subplot(3, 3, i+1)
        plot_nstations_timeseries(varnames, repo_folder, ax=ax)
    ax = plt.subplot(3, 3, 9)
    plot_nstations_timeseries_vmro3max(repo_folder, ax=ax)
    fig.subplots_adjust(hspace=.6, wspace=.3)
    plt.suptitle('Number of stations with data as function of time', fontsize=16)
    # Save figure
    fig.savefig(figfile, bbox_inches='tight', dpi=200)
    plt.close(fig)
    print('Saved figure to %s' % figfile)
