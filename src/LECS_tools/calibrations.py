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
do_cal_coeffs = dict(
A_o2 = -4.382235e01,
B_o2 = 1.398755e02,
C_o2 = -4.119456e-01,
D_o2 = 9.934000e-03,
E_o2 = 4.000000e-03,
F_o2 = 4.440000e-05,
G_o2 = 0.000000e+00,
H_o2 = 1.000000e+00,
)

def convert_raw_o2(voltO2,temp,cal_coeffs=do_cal_coeffs):
    """
    
    
    """
    
    Pprime = ((cal_coeffs['A_o2']) /( 1 + cal_coeffs['D_o2']*(temp -25))) + (cal_coeffs['B_o2'] / ((voltO2 - cal_coeffs['F_o2'])*(1+cal_coeffs['D_o2']*(temp -25)) + cal_coeffs['C_o2'] + cal_coeffs['F_o2']))
    do_percent = cal_coeffs['G_o2'] + cal_coeffs['H_o2'] * Pprime
    return do_percent


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
    
        
    