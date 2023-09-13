"""  
Created By Manish Devana

Tools for flux calculations from eddy covariance measurements

"""

import pandas as pd
import numpy as np
import scipy.signal as signal 
import scipy.integrate as integrate
import xarray as xr




def spectralECflux(df, x1, x2 freq='60min', fs=16, windowMinutes=30, high=0.125, low=1/(15*60)):
    """_summary_

    Args:
        x1 (_type_): takes in data frame of variable 1
        x2 (_type_): data frame of variable 1

    Returns:
        _type_: eddy covariance flux
        timeS: time stamps of fluxes
    """
    
    # spectral parameters
    window_length_seconds = windowMinutes*60
    nperseg = window_length_seconds//(1/fs)
    
    dfGrouped =  df.groupby(pd.Grouper(freq=freq, key='time'), as_index=False, dropna=False)
    flux = []
    fluxTimes = []
    
    for timestamp, dfIn in dfGrouped.__iter__():   
        if (dfIn[x1].values.shape[0] > nperseg) and (dfIn[x2].values.shape[0] > nperseg):
            fluxTimes.append(dfIn.time.mean())
            f, psd  = signal.csd(
                dfIn[x1].values,
                dfIn[x2].values,
                fs=fs,
                nperseg=len(dfIn[x1].values)/2,
                noverlap=None, ## default is 50%
                
            
        )
        
            mask1 = f>=low
            mask2 = f<= high
            mask = np.logical_and(mask1, mask2)
            

            tt = integrate.trapezoid(np.real(psd[mask]), f[mask])*60*60 ## convert to hourly (still need to apply whatever other unit changes you neeed
            flux.append(tt)

                
    
    return np.hstack(flux), np.hstack(fluxTimes)



