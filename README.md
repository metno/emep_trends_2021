# emep_trends_2021
Code for trends processing for EMEP 2021 report

The repository contains the code for reading EBAS observation data and EMEP model output and creating colocated time series from which trends are calculated.

Trend analysis is done for monthly mean of a large number of variables. For ozone concentration the trend analysis is instead done for a number of annual percentiles of daily max.

Resampling from hourly to daily is done for days with at least 18 hours of observation data. Resampling from daily/weekly to monthly is done with two different resampling constraints:
- strict constraint: At least 21 days or 3 weeks
- relaxed constraint: At least 4 days or 2 weeks

Output data from the analysis is stored in separate repositories from this one. The data with strict resampling constraints is stored in:   

https://github.com/metno/emep_trends_2021_data

The data with relaxed constraints is stored in: 

https://github.com/metno/emep_trends_2021_data_relaxed

The pyaerocom version used for the processing can be downloaded here:

https://github.com/metno/pyaerocom/releases/tag/v0.12.0dev2
