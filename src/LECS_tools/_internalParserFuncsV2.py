""" 
Internal parsing functions for the parser.
- Revised version that uses the datetime stamps from the ADV


"""



import numpy as np
import pandas as pd
import datetime as dt
from urllib.request import urlopen
from tqdm import tqdm as bar

### params for parsing
# RINKO_CALS_temp - for the serial number 
A = -1.219367e1
B = 2.134089e1
C = -3.559172e00
D = 6.691104e-01

## RINK_CALS_DO (SENSING FILM A)
A_o2 = -4.382235e01
B_o2 = 1.398755e02
C_o2 = -4.119456e-01
D_o2 = 9.934000e-03
E_o2 = 4.000000e-03
F_o2 = 4.440000e-05
G_o2 = 0.000000e+00
H_o2 = 1.000000e+00


## Dline variable names from the raw LECS data
namesDline = (
    'count',
    'pressure',
    'u',
    'v',
    'w',
    'amp1', # amplitude of 1st beam
    'amp2', # amplitude of 2nd beam
    'amp3', # amplitude of 3rd beam
    'corr1', # correlation of 1st beam
    'corr2', # correlation of 2nd beam
    'corr3', # correlation of 3rd beam
    'sync1', # unclear what this is
    'unknown1', # unclear what this is
    'ph_raw_voltage', # raw voltage of ph
    'temp', # temperature offset by x0.1
    'DO'
    
)

slineKey =[
    'hour',
    'minute',
    'second',
    'day',
    'month',
    'year',
    'minuteVSD', 'secondVSD', 'dayVSD', 'hourVSD', 'yearVSD', 'monthVSD', # not sure these values are good rn
    'batteryVoltage',
    'soundSpeed',
    'heading',
    'pitch',
    'roll' ,
    'temp2',   
    ]

dLineFullLength = len(namesDline)

def loadLECSdata(url='https://gems.whoi.edu/LECSrawdata/'):
    """
    This function loads the raw data printed to the raw data page on the LECS website.
    Its useful for testing parsing but its really an artefact of the old methods.
    """
    fid=urlopen('https://gems.whoi.edu/LECSrawdata/')
    dataLines = []
    webpage=fid.read().decode('utf-8')
    # # print(webpage)
    for line in bar(webpage.split('\n')):
        # print(line)
        # print('------------------')
        
        if '<td>' in line and '</td>' in line:
            dataLines.append(line)

    ii = 0
    DlinesPre = []
    SlinesPre = []
    gpsPre = []
    idx = 0
    for l in bar(dataLines[500:]):
        # print(
        l = l.replace('<td>','').replace('</td>','')
        # print(str(ii) + ':' + l)
        l = l.strip()
        # if 'D:' in l:
        #     DlinesPre.append(l)
        # elif 'S:' in l:
        #     SlinesPre.append(l)
        # elif '$' in l:
        #     gpsPre.append(l)
        if 'D:' in l:
            DlinesPre.append((idx, l))
        elif 'S:' in l:
            SlinesPre.append((idx,l))
        elif '$' in l:
            gpsPre.append((idx,l))
        idx += 1    
            
        ii+=1
            
    return DlinesPre, SlinesPre, gpsPre


def DlineParser(dlinesList, 
                correctNumEntries = 16,
                names = namesDline,
                ):
    """
    This function parses the D lines (Data lines) from the LECS raw data and returns a pandas dataframe.
    It also applies the calibration coefficients to the data.
    A follow up step is required to align the data with the S lines (status lines) which contain the timestamps.
    This is done in the function alignTimeWithData.
    Args:
        dlinesList (list): List of D-line strings
        correctNumEntries (int, optional): number of data points in each line. Defaults to 16.
        names (_type_, optional): names of the data columns. Defaults to namesDline.

    Returns:
        _type_: _description_
    """
    
    # dline parser data entries
    
    # first filter out bad lines (missing value lines)
    df = []
    sep = 'D:'
    counts = []
    Dlines = []
    idxArray = []
    for idx, line in dlinesList:
        
        
        if line[-1] == '.':
            line = line[:-1]
        t = line.split(sep, 1)[1]
        # print(t)
        # print(len(t.split(',')))
        
        counts.append(len(t.split(',')))
        if len(t.split(',')) ==16:
            Dlines.append(t.split(','))
            idxArray.append(idx)
        
    idxArray = np.hstack(idxArray)
    # now stack the data into a dataframe
    DlineArray = np.vstack(Dlines)
    DlineDataFrame = pd.DataFrame(DlineArray, 
                                  columns = names,dtype=float)
    
    ## apply corrections
    DlineDataFrame['u'] = DlineDataFrame['u'] * 0.001
    DlineDataFrame['v'] = DlineDataFrame['v'] * 0.001
    DlineDataFrame['w'] = DlineDataFrame['w'] * 0.001
    Volt = DlineDataFrame['temp']
    voltO2 = DlineDataFrame['DO']
    DlineDataFrame['temp'] = A+B*Volt+C*Volt**2+D*Volt**3
    Pprime = ((A_o2) /( 1 + D_o2*(DlineDataFrame['temp'] -25))) + ((B_o2) / ((voltO2 - F_o2)*(1+D_o2*(DlineDataFrame['temp'] -25)) + C_o2 + F_o2))
    DlineDataFrame['DO_percent'] = G_o2 + H_o2 * Pprime
    
    DlineDataFrame.set_index(idxArray,inplace=True)
    # print(DlineDataFrame.head())
    
    return DlineDataFrame
    # for line in dlinesList:
        
    
    # return parsedDlines

    
def SlineParser(slinesList,timeOnly=True):
    """
    parse the S lines and turn them into timestamps
    
    

    Args:
        slinesList (_type_): _description_
    """
    
    # first parse all the slines
    sep = 'S:'
    SlineArray = []
    idxArray = []
    if timeOnly:
        for idx, line in slinesList:
            t = line.split(sep, 1)[1] # split the line by the separator
            SlineArray.append(t.split(',')[:18]) # split the line by commas including only the time
            idxArray.append(idx)
            
        idxArray = np.hstack(idxArray)
        SlineArray = np.vstack(SlineArray)
        SlineDataFrame = pd.DataFrame(SlineArray, 
                                    columns = slineKey, dtype=float)
        SlineDataFrame['yearVSD'] = SlineDataFrame['yearVSD'] + 2000
        SlineDataFrame.set_index(idxArray,inplace=True) # set the index to the original index

        SlineDataFrame = SlineDataFrame[SlineDataFrame['yearVSD'] >= 2022]
        SlineDataFrame = SlineDataFrame[SlineDataFrame['yearVSD'] <= 2024]
        SlineDataFrame = SlineDataFrame[SlineDataFrame['monthVSD'] <= 12]
        SlineDataFrame = SlineDataFrame[SlineDataFrame['dayVSD'] <= 31]


        time = pd.to_datetime(SlineDataFrame[['year','month','day','hour','minute','second']])

        # adve time parsing - have to change the names
        tPre = SlineDataFrame[['yearVSD','monthVSD','dayVSD','hourVSD','minuteVSD','secondVSD']]
        namesPre = list(tPre.columns)
        for i, name in enumerate(tPre.columns):
            tPre = tPre.rename(columns={name:namesPre[i][:-3]})

        timeADV = pd.to_datetime(tPre)
        SlineDataFrame['time'] = time # convert the time to timestamps
        SlineDataFrame['timeADV'] = timeADV
        
        SlineDataFrame = SlineDataFrame.where(SlineDataFrame['time'] < pd.to_datetime('now'))
        SlineDataFrame = SlineDataFrame.where(SlineDataFrame['timeADV'] < pd.to_datetime('now'))

        return SlineDataFrame 
    
    else: # this is really unused junk right now
        for idx, line in slinesList:
            t = line.split(sep, 1)[1] # split the line by the separator
            SlineArray.append(t.split(',')[:6]) # split the line by commas including only the time
        return SlineArray
        
    # now stack the data into a dataframe
    # SlineArray = np.vstack(SlineArray) 
    # SlineDataFrame = pd.DataFrame(SlineArray, 
    #                               columns = namesSline,dtype=float)
    
    # return SlineArray
    
    

def alignTimeWithData(data, sLines, useCount2sort=False,
                      samplingFrequencyHz=16,
                      lowTimeCutoff='2022', highTimeCutoff='now'):
    """
    
    

    Args:
        data (_type_): _description_
        time (_type_): _description_
    """
    # add an empty column to the data and fill with time values at indicies that are aligned
    timestep = pd.Timedelta(1/samplingFrequencyHz, unit='s')
    dataRev = data.copy()
    
    if useCount2sort:
        # Loop throough the slines and start filling inthe time values
        for kk, ix in enumerate(sLines.index.values.astype(int)[:-1]):
            
            # if the s line corresponds to data in following lines
            if ix+1 in data.index.values.astype(int):
                
                # set the range of data to span from this S line to the next
                nextSline = sLines.index.values.astype(int)[kk+1]-1
                # print(nextSline-ix)
                
                # Start the counter at the first value in the next line
                count0 = data.loc[ix+1, 'count']
                
                # use the Sline to set t0
                newTime = sLines.loc[ix, 'time'] 
                
                # start the time using t0
                dataRev.loc[ix+1, 'time'] = newTime
                
                # increment by the sampling frequency + the count difference (need the count differnece to account for missing data)
                for ii in range(ix+2, nextSline+1):
                    if ii in data.index.values.astype(int):
                        countIn = data.loc[ii, 'count']
                        
                        # bad data has counts over 260, ignore those lines
                        if countIn < 260:
                            
                            # if the count is counting up
                            if countIn > count0:
                                # difference between current count and starting count for this section
                                countDelta = countIn - count0
                                if countDelta < 0:
                                    print('fuck')
                                    raise RuntimeError('countDelta is negative')
                                
                                # calculate the time by adding time
                                newTime = newTime + timestep * countDelta
                                dataRev.loc[ii, 'time'] = newTime
                                
                            # if the count rolls over set the count start back to the current count
                            # and increment the time by one timestep but change t0 to the last steps time before the rollover
                            elif countIn < count0:
                                count0 = countIn
                                countDelta = countIn - count0
                                newTimeB = newTime + timestep * (countDelta+1)
                                if newTimeB < newTime:
                                    print('fuck')
                                    raise RuntimeError('newTimeB is less than newTime')
                                dataRev.loc[ii, 'time'] = newTimeB
        
    
    
    else:
        print('ignore counts')
        for kk, ix in enumerate(sLines.index.values.astype(int)[:-1]):
            # if the s line corresponds to data in following lines
            cc = 1
            if ix+1 in data.index.values.astype(int):
                # set the range of data to span from this S line to the next
                nextSline = sLines.index.values.astype(int)[kk+1]-1
                # print(nextSline-ix)
        
                # use the Sline to set t0
                newTime = sLines.loc[ix, 'time'] 
                
                # start the time using t0
                dataRev.loc[ix+1, 'time'] = newTime
                
                # increment by the sampling frequency + the count difference (need the count differnece to account for missing data)
                for ii in range(ix+2, nextSline+1):
                    if ii in data.index.values.astype(int):
                        
                        newTime = newTime + timestep * cc
                        dataRev.loc[ii, 'time'] = newTime
                        
                        
        ## apply time cutoffs
    dataRev[pd.to_datetime(dataRev.time) > np.datetime64(highTimeCutoff)] = np.datetime64('NaT')
    dataRev[pd.to_datetime(dataRev.time) < np.datetime64(lowTimeCutoff)] = np.datetime64('NaT')

    return dataRev.sort_values(by='time')

def timeAlignmentV2(data, sLines,
                      samplingFrequencyHz=16,
                      lowTimeCutoff='2022', highTimeCutoff='now'):
    """


    Returns:

    """
    # add an empty column to the data and fill with time values at indicies that are aligned
    timestep = pd.Timedelta(1/samplingFrequencyHz, unit='s')
    dataRev = data.copy()

    for kk, ix in enumerate(sLines.index.values.astype(int)[:-1]): ## loop through the lines
        # if the s line corresponds to data in following lines
        cc = 1
        if ix + 1 in data.index.values.astype(int):
            # set the range of data to span from this S line to the next
            nextSline = sLines.index.values.astype(int)[kk + 1] - 1
            # use the Sline to set t0
            newTime = sLines.loc[ix, 'timeADV']
            # start the time using t0
            dataRev.loc[ix + 1, 'time'] = newTime
            # Start the counter at the first value in the next line
            count0 = dataRev.loc[ix+1, 'count']
            # increment by the sampling frequency + the count difference (need the count differnece to account for missing data)
            for ii in range(ix + 2, nextSline + 1):
                if ii in data.index.values.astype(int):
                    countIn = dataRev .loc[ii, 'count']
                    if countIn < 256: # IGNORE HIGHER COUNTS SINCE IT MEANS BAD DATA
                        newTime = newTime + timestep * cc
                        dataRev.loc[ii, 'time'] = newTime

                        # if the count is counting up
                        if countIn > count0:
                            # difference between current count and starting count for this section
                            countDelta = countIn - count0  # this is in case any counts are skipped
                            if countDelta < 0:  # this should never happen
                                print('fuck')
                                raise RuntimeError('countDelta is negative')

                            # calculate the time by adding time
                            newTime = newTime + timestep * countDelta
                            dataRev.loc[ii, 'time'] = newTime

                            # if the count rolls over set the count start back to the current count
                            # and increment the time by one timestep but change t0 to the last steps time before the rollover
                        elif countIn < count0:
                            count0 = countIn
                            countDelta = countIn - count0
                            newTimeB = newTime + timestep * (countDelta + 1)
                            if newTimeB < newTime:
                                print('fuck')
                                raise RuntimeError('newTimeB is less than newTime')
                            dataRev.loc[ii, 'time'] = newTimeB



        ## apply time cutoffs
    dataRev[pd.to_datetime(dataRev.time) > np.datetime64(highTimeCutoff)] = np.datetime64('NaT')
    dataRev[pd.to_datetime(dataRev.time) < np.datetime64(lowTimeCutoff)] = np.datetime64('NaT')

    return dataRev.sort_values(by='time')





###################
###################
###################
###################

def parseDatabaseLines(dataLines, barFlag=False):
    """
    
    """
    
    ii = 0
    DlinesPre = []
    SlinesPre = []
    gpsPre = []
    idx = 0
    # print('Splitting D and Slines')
    for l in bar(dataLines, disable=True):
        # print(
        # l = l.replace('<td>','').replace('</td>','')
        # print(str(ii) + ':' + l)
        l = l.strip()
        # if 'D:' in l:
        #     DlinesPre.append(l)
        # elif 'S:' in l:
        #     SlinesPre.append(l)
        # elif '$' in l:
        #     gpsPre.append(l)
        if 'D:' in l:
            DlinesPre.append((idx, l))
        elif 'S:' in l:
            SlinesPre.append((idx,l))
        elif '$' in l:
            gpsPre.append((idx,l))
        idx += 1    
            
        ii+=1
            
    # DlinesPre, SlinesPre, gpsPre ## thiis the results of part1 but I am baking it all into one function here
    # print('Parse D lines')
    # print(DlinesPre)
    Dlines = DlineParser(DlinesPre)
    # print('Parse S lines')
    Slines = SlineParser(SlinesPre)
    # print(Slines.head())
    Dlines = timeAlignmentV2(Dlines, Slines)
    # print(Dlines.head())
    parsedDataframe = Dlines[~np.isnat(Dlines.time)]
    sDataFrame = Slines[~np.isnat(Slines.time)]
    
    # return Slines, Dlines
    return parsedDataframe, sDataFrame
