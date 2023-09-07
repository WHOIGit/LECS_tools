""" 
Created By Manish Devana

tools for running calibrations

"""


from curses import raw
import numpy as np
from sklearn.linear_model import LinearRegression
import pandas as pd
import json
import os




def phCal_multiVarLinReg_ph_temp(rawPhCounts,temp, calCoeffs=None,**kwargs):
    """
    

    Args:
        rawPhCounts (_type_): _description_
        calCoeffs (_type_, optional): _description_. json file with linear regression coeffs, Defaults to None.
        
    Returns: 
        ph: cl
    """
    
    
    if calCoeffs is None:
        raise ValueError("calCoeffs must be provided... Future versions will include automated seaphox data calibration")
    
    else:
        jsonFile = open(calCoeffs)
        calDict = json.load(jsonFile)

        model = LinearRegression()
        model.coef_ = np.array(calDict['coef_'])
        model.intercept_ = np.array(calDict['intercept_'])
        inputs = np.vstack([
            rawPhCounts,
            temp
        ]).T
        ph = model.predict(inputs)
        
        return ph
    
        
    