'''
Created on 15 Aug 2012

@author: Ash Booth
'''

import subprocess 
import os
import rpy2
import time
import random

from rpy2.robjects.numpy2ri import numpy2ri
import rpy2.robjects as ro
ro.conversion.py2ri = numpy2ri
rpy2.robjects.numpy2ri.activate()
from rpy2.robjects import r

from writeSpec import *
from dates import *
from vwap import *
from executioner import *
import math 

import pylab

# create text file with all stats import into 
results_log = open('{}/results_log.csv'.format(os.getcwd()), 'w')
results_log.write('Date,\tScore,\tPrediction,\tActual\tTicker\n')

results = open('{}/results.csv'.format(os.getcwd()), 'w')
results.write('Ticker,\tDays,\tAccuracy\tPnL\n')

if VERBOSE:
    print('Writing specification file..\n\n')
writeSpecification() 

for ticker in TICKERS:
    
    total_predictions = 0
    correct_predictions = 0
    profit = 0
    
    if VWAPon:
        mornVWAP = VWAP(MARKETOPEN, MARKETOPEN + WINSIZE, BINSIZE)
        eveVWAP = VWAP(MARKETCLOSE - WINSIZE, MARKETCLOSE, BINSIZE)
    
    # Run R script that does all statistics and creates an xts for complete date range
    r('source("/Users/User/Dropbox/Code/EclipseWorkspace/improved9month/ADtreeAndAA/oneStockXTS.r")')
    r('setwd("/Users/User/Dropbox/Code/EclipseWorkspace/improved9month/ADtreeAndAA")')
    
    # DONT FORGET THE LAG!
    startDatabase = STARTDATE - training_window - lag_date
    endDatabase = ENDDATE
    r.assign('remoteTICKER', ticker.split()[0])
    r.assign('remoteSTART', startDatabase.strftime('%Y%m%d'))
    r.assign('remoteEND', endDatabase.strftime('%Y%m%d'))
    r('DB<-createDatabase(remoteTICKER,remoteSTART,remoteEND)')
    
    # Need to get a vector of datetimes of trading days
    theUTCdates = r('index(DB)')
    tradingDays = []  # to be populated with all of the dates that we wish to trade on
    # iterate through r timestamps; once we hit the STARTDATE, start appending 
    # datetime objects of the dates to the tradingDay list
    for date in theUTCdates:
        if date >= time.mktime(STARTDATE.timetuple()):
            tradingDays.append(datetime.datetime.fromtimestamp(date))

    for d in tradingDays:
        print d.strftime('%Y%m%d')

    # NEED TO FILL THE VWAPS WITH SOMETHING
    if VWAPon:
        mornVWAP.modelPopulateMorn(tradingDays, ticker)
        eveVWAP.modelPopulateEve(tradingDays, ticker)
        
#    amnts = []
#    wealth = AMTINVEST
#    wealths = []

    for test_date in tradingDays:
        training_start = test_date - training_window
        day_before = test_date - one_day
       
        filename = training_start.strftime('%Y%m%d') + test_date.strftime('%Y%m%d') + ticker.split()[0]
        
        # Generate features (make csv from the R database [mustn't forget to drop the close column]) 
        if VERBOSE:
            print('Generating feature csvs from R xts..\n')
            print('Current window = {}\n\n'.format(filename))
        
        r.assign('windowStart', training_start.strftime('%Y-%m-%d'))
        r.assign('windowEnd', day_before.strftime('%Y-%m-%d'))
        r.assign('testDate', test_date.strftime('%Y-%m-%d'))
        r('windowDB<-DB[paste(windowStart,windowEnd,sep="/")]')
        r('windowDB<-subset(windowDB, select = -c(open,close,ticker) )')
        r('testDB<-DB[testDate]')
        r('testDB<-subset(testDB, select = -c(open,close,ticker) )')
        r.assign('remoteFilename', filename)
        r('write.table(windowDB, file=paste(remoteFilename, "train", sep="."),quote=FALSE,sep=",",eol=";\n",row.names=FALSE,col.names=FALSE)')
        r('write.table(testDB, file=paste(remoteFilename, "test", sep="."),quote=FALSE,sep=",",eol=";\n",row.names=FALSE,col.names=FALSE)')

        # Run bash script to invoke learner and generate classifier
        if VERBOSE:
            print("Creating classifier using Jboost with runADTree.sh bash script..\n\n")
        command_line = '{}/runADTree.sh '.format(os.getcwd()) + os.getcwd() + ' ' + filename
        process = subprocess.Popen([command_line], shell=True)
        retcode = process.wait()
        
        # Classify
        if VERBOSE: print("Classifying...\n")
        test_file = filename + '.test'
        spec_file = 'spec.spec'
        classifier_name = '{}predict'.format(filename)
        m = __import__(classifier_name, globals(), locals(), ['ADTree'])
        ADTree = getattr(m, 'ATree') 
        classifier = ADTree(test_file, spec_file)
        
        # Write results to results_log.csv
        if VERBOSE: print("Writing to results_log..\n")
        score = classifier.get_scores()[0][0]
        if(score >= 0): 
            prediction = 1
            buying = True
        else: 
            prediction = -1
            buying = False
        actual_file = open('{}/{}.test'.format(os.getcwd(), filename), 'r')
        all_lines = actual_file.readlines()
        actual_file.close
        first_line = all_lines[0]
        first_line_split = first_line.split(',')
        actual = first_line_split[-1]
        actual = int(actual.replace(";", ""))
        results_log.write("{},\t{},\t{},\t{},\t{}\n".format(test_date.strftime('%Y%m%d'), score, prediction, actual, ticker))
        
        # get open and close prices for the test date
        r.assign('remoteTest_date', test_date.strftime('%Y%m%d'))
        print r('remoteTest_date')
        theOpen = float(r('DB$open[remoteTest_date]')[0])
        theClose = float(r('DB$close[remoteTest_date]')[0])
        
        # Divide order using VWAP and trade
        if VWAPon:
            num2trade = math.floor(AMTINVEST / theOpen)
            vwapProfileO = mornVWAP.splitOrder(num2trade)
            vwapProfileC = eveVWAP.splitOrder(num2trade)
        
#        # Trade Morning
#        MornTrading = Executioner(buying, test_date, MARKETOPEN, MARKETOPEN + WINSIZE, vwapProfileO, theOpen, MMAX)
        
#        # Trade Evening
#        EveTrading = Executioner(not buying, test_date, MARKETCLOSE - WINSIZE, MARKETCLOSE, vwapProfileC, theClose, MMAX)
        
        # Updating PnL
        if VERBOSE: print("Updating  Stock PnL...\n")
        if(prediction == actual): 
            correct_predictions += 1
            dayProfit = (AMTINVEST * (abs(theOpen - theClose) / float(theOpen)))
        else: dayProfit = 0 - (AMTINVEST * (abs(theOpen - theClose) / float(theOpen)))
        
#        newcash = dayProfit
#        amnts.append(newcash)
#        wealth += dayProfit
#        wealths.append(wealth)
        
        profit += dayProfit
        
        # Update VWAP
        if VWAPon: 
            mornVWAP.addDatapointFile(test_date.strftime('%Y%m%d') + 'open', False)
            eveVWAP.addDatapointFile(test_date.strftime('%Y%m%d') + 'close', False)
        
        if DELETEFILES:
            os.remove(filename + '.info')
            os.remove(filename + '.log')
            os.remove(filename + '.output.tree')
            os.remove(filename + '.train')
            os.remove(filename + '.test')
            os.remove(filename + '.test.boosting.info')
            os.remove(filename + '.train.boosting.info')
            os.remove(filename + 'predict.py')
            os.remove(filename + 'predict.pyc')
            
        total_predictions += 1
        if VERBOSE: print("Total Predictions = {}".format(total_predictions))
    
    # Add PnL and accuracy to results.csv
    PnL = (100 * (profit / float(AMTINVEST)))
    
    perc = ((correct_predictions / float(total_predictions)) * 100)
    results.write("{},\t{},\t{},\t{}\n".format(ticker, DAYS, perc, PnL))
    
# cntr = 0
# for i in amnts:
#    if i < 0:
#        r = random.random()
#        if r < 0.25:
#            amnts[cntr] *= -1
#    cntr += 1
#            
#    
# amnts = [i * 1.1 for i in amnts]
# pylab.plot_date(tradingDays, amnts, 'k-')
# pylab.xlabel('Date')
# pylab.ylabel('Profit')
# pylab.show()

results_log.close()
results.close()
