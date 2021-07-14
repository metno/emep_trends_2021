#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jun 23 10:17:17 2021

@author: jonasg
"""
import os, shutil, glob


def delete_outdated_output(outdir, varlist):
    files = glob.glob(f'{outdir}/sitemeta*.csv')
    for file in files:
        fname = os.path.basename(file)
        var = fname.split('_')[-1].split('.csv')[0]
        if var not in varlist:
            clear_output(outdir, var)


def clear_output(outdir, var):
    files = glob.glob(f'{outdir}/*{var}*.csv')
    if len(files) > 0:
        print(f'delete output for {var} in {outdir}')
    for file in files:
        os.remove(file)

    datadir = os.path.join(outdir, f'data_{var}')
    if os.path.exists(datadir):
        shutil.rmtree(datadir)


def get_years_to_read(periods):
    """
    Get the range in years to be read to cover given periods.

    The periods are left- and right-inclusive, while returned range of years
    is only left-inclusive. The range will go from the year before the first
    year occurring in any period, in order to include the whole winter season
    of the first year (which includes December of the previous year).
    The 'stop' year in the range is one year after the last year included in
    any of the periods, so that looping over this range will include the last
    year in all periods.

    Parameters
    ----------
    periods : list of len-3 tuples
        Elements of the tuples are first and last year of the periods.
        The third element is not used by this function.

    Returns
    -------
    start_str : string
        String representation of the first year to read
    stop_str : string
        String representation of the year after the last year to read
    """
    first = 2100
    last = 1900
    for st, end, _ in periods:
        if st < first:
            first = st
        if end > last:
            last = end
    start_str = str(first-1)
    stop_str = str(last+1)
    return start_str, stop_str
