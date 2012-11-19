'''
Created on 9 Oct 2012

@author: Ash Booth
'''
import datetime 
import dates
import pylab
import os

class VolWindow(object):
    def __init__(self, start, end):
        self.start = start
        self.end = end
        self.totalVol = 0
        self.vwap = 0.0
        self.totalVolByPrice = 0
        self.volProfile = 0
        self.dataPoints = 0
        
    def timeInWindow(self, t):
        if(self.start <= t < self.end):
            return True
        else: return False
        
    def endDay(self):
        self.dataPoints += 1
        self.volProfile = self.totalVol / float(self.dataPoints)
        self.vwap = self.totalVolByPrice / float(self.totalVol)
        
    
class VWAP(object):
    def __init__(self, start, end, bin_size):
        """
        start and end are date times, break is a timeDelta
        """
        self.start = start.time()
        self.end = end.time()
        self.bin_size = bin_size
        self.volWindows = []
        for time in dates.timeRange(start, end, bin_size):
            self.volWindows.append(VolWindow(time.time(), (time + bin_size).time()))
            
    def addTrade(self, time, vol):
        for bins in self.volWindows:
            if time < bins.end:
                bins.totalVol += vol
                break
        
    def endOfDay(self):
        for bins in self.volWindows:
            bins.endDay()
    
    def addDatapointFile(self, filename, verbose):
        # open file with historical data
        try:
            fullname = filename
            reader = open(fullname, 'rU')
            for line in reader:
                # line should look like this:
                # timestamp, type, price, volume
                split = line.split(',')
                if (split[1] == 'TRADE'):
                    dt = datetime.datetime.strptime(split[0], "%Y-%m-%d %H:%M:%S")
                    t = dt.time()
                    vol = int (split[3])
                    price = float (split[2])
                    for bins in self.volWindows:
                        if t < bins.end:
                            bins.totalVol += vol
                            bins.totalVolByPrice += (vol*price)
                            break
            reader.close()
            
            # Update number of datapoints and the VWAP profile
            self.endOfDay()
            if verbose: print "File successfully read"
        except IOError:
            print 'Cannot open input file "{}"'.format(fullname)
            
    def getProfile(self):
        return self.volWindows
        
    def getVols(self, verbose):
        vols = []
        for w in self.volWindows:
            vols.append(w.volProfile)
            if verbose: print w.volProfile
        return vols
    
    def getBinVWAPS(self):
        vwaps = []
        for w in self.volWindows:
            vwaps.append(w.vwap)
        return vwaps
    
    def splitOrder(self, totalTradeSize):
        '''
        Return a list of Vol window objects with the sizes corresponding to fractions 
        of your trade splitt acording to the current VWAP profile
        '''
        profile = self.getProfile(False)
        perc = totalTradeSize / float(sum(window.volProfile for window in profile))
        for i in profile:
            i.volProfile = (int (i.volProfile * perc))
        return profile
    
    def plotProfile(self):
        pylab.plot(self.getVols(False))
        pylab.show()
        
    def modelPopulateMorn(self, tradingdays, ticker):
        for d in tradingdays:
            self.addDatapointFile(os.getcwd() + '/tickData/' + d.strftime('%Y%m%d') + ticker + 'open', False)
    
    def modelPopulateEve(self, tradingdays, ticker):
        for d in tradingdays:
            self.addDatapointFile(os.getcwd() + '/tickData/' + d.strftime('%Y%m%d') + ticker + 'close', False)

# Test the VWAP
# MARKETOPEN = datetime.datetime.strptime('19/09/2012  14:30:00', "%d/%m/%Y %H:%M:%S")
# MARKETCLOSE = datetime.datetime.strptime('19/09/2012  15:00:00', "%d/%m/%Y %H:%M:%S")
# WINSIZE = datetime.timedelta(minutes=30)
# BINSIZE = datetime.timedelta(minutes=5)
#
# test_days = ['20120801', '20120802', '20120803', '20120806', '20120807', '20120808', '20120809']
# test_daysDT = []
# for d in test_days: test_daysDT.append(datetime.datetime.strptime(d, "%Y%m%d"))
#
# mornVWAP = VWAP(MARKETOPEN, MARKETOPEN + WINSIZE, BINSIZE)
# eveVWAP = VWAP(MARKETCLOSE - WINSIZE, MARKETCLOSE, BINSIZE)
#
# mornVWAP.modelPopulateMorn(test_daysDT, 'GOOG')
# eveVWAP.modelPopulateEve(test_daysDT, 'GOOG')
#
# print mornVWAP.getProfile(False)
# pylab.plot(mornVWAP.getProfile(False))
# pylab.show()
