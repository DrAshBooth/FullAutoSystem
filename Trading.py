'''
Created on 24 Oct 2012

@author: Ash Booth
'''
from executioner import *

import datetime

class Trading(object):
    '''
    classdocs
    '''
    
    def __init__(self, buying, date, start, end, volProfiles, filename, openPrice,params):
        '''
        Constructor
        '''
        self.buying = buying
        self.date = date
        self.volProfiles = volProfiles
        self.start = start
        self.end = end
        self.filename = filename
        self.limit = openPrice
        self.trades = []
        self.dcash = 0
        self.params=params
        
#    def tradeReport(self):
#        nonelocations = []
#        ncntr = 0
#        cashDelta = 0
#        totVol = 0
#        for i in range(len(self.trades)):
#            if self.trades[i] == None:
#                nonelocations.append(i)
#                ncntr += 1
#            else:
#                totVol += self.volProfiles[i].volProfile
#                cashDelta += (self.trades[i] * self.volProfiles[i].volProfile)
#        # What about the nones?? This is a hack that replaces periods that we didn't trade wit the vwap
#        vwap = cashDelta / float(totVol)
#        for i in nonelocations:
#            cashDelta += (vwap * self.volProfiles[i].volProfile)
#        
#        # Buying or selling?
#        if self.buying: return -1 * cashDelta
#        else: return cashDelta
        
#    def WhatsMyVWAP(self):
#        cashDelta = 0
#        totVol = 0
#        for i in range(len(self.trades)):
#            if not(self.trades[i] == None):
#                totVol += self.volProfiles[i].volProfile
#                cashDelta += (self.trades[i] * self.volProfiles[i].volProfile)
#        # What about the nones?? This is a hack that replaces periods that we didn't trade wit the vwap
#        myVWAP = cashDelta / float(totVol)
#        return myVWAP
    
    def trade(self):
        noBB = True
        noBA = True
        bestBid = None
        bestAsk = None
        tempEP = None
        noPriceSeen = True
        firstTime = True
        currentWindow = 0
        try: 
            f = open(self.filename, 'rU')
            for line in f:
                # line should look like this:
                # timestamp, type, price, volume
                splitLine = line.split(',')
                dt = datetime.datetime.strptime(splitLine[0], "%Y-%m-%d %H:%M:%S")
                time = dt.time()
                event = splitLine[1]
                price = float(splitLine[2])
                if(noBB or noBA):
                    if (event == 'BEST_BID'):
                        noBB = False
                        bestBid = price
                        continue
                    if (event == 'BEST_ASK'):
                        noBA = False
                        bestAsk = price
                        continue
                    if (event == 'TRADE'):
                        if noPriceSeen:
                            tempEP = price
                            noPriceSeen = False
                        else: tempEP = tempEP * price + (1 - 0.3) * 0.3
                        continue
                if tempEP == None: tempEP = price
                    
                if firstTime: 
                    theExecutioner = Executioner(dt.date(), time, self.buying, self.volProfiles[0].start,
                                                 self.volProfiles[0].end, self.volProfiles[0].volProfile,
                                                 tempEP, bestBid, bestAsk, 2 * tempEP, -6, self.limit ,
                                                 (1.03 * tempEP) - (0.1 * tempEP * int(self.buying)),
                                                 0.1, -0.5, self.params)
                firstTime = False
                # Now have enough info to start
                # Are we in a new time period?
                if time > self.volProfiles[currentWindow].end:
                    self.trades.append(theExecutioner.getTradeResults())
                    theExecutioner = Executioner(dt.date(), time, self.buying,
                                                 self.volProfiles[currentWindow + 1].start,
                                                 self.volProfiles[currentWindow + 1].end,
                                                 self.volProfiles[currentWindow + 1].volProfile, 
                                                 theExecutioner.eqlbm, theExecutioner.currentBid,
                                                 theExecutioner.currentAsk, theExecutioner.marketMax, 
                                                 theExecutioner.theta, theExecutioner.limit,
                                                 theExecutioner.target, theExecutioner.smithsAlpha,
                                                 theExecutioner.aggressiveness, self.params)
                    currentWindow += 1
                
                # What happened? trade? updated bid? or updated ask?
                trade = None
                bid = None
                if (event == 'TRADE'): trade = True
                elif (event == 'BEST_BID'):
                    trade = False
                    bid = True
                elif (event == 'BEST_ASK'):
                    trade = False
                    bid = False
                theExecutioner.newInfo(time, price, trade, bid)
            self.trades.append(theExecutioner.getTradeResults())
            f.close()
        except IOError:
            print "\nCannot open trade/BB/BA file:\t" + self.filename


##########################################################
######################### Testing ########################
##########################################################
#
# from vwap import *
#
# # Open trade data file
# date = datetime.datetime.strptime('2012-06-21', "%Y-%m-%d")
# filename = os.getcwd() + '/tickData/20120621AAPL US Equityopen.csv'
# start = datetime.datetime.strptime('2012-06-21 13:30:00', "%Y-%m-%d %H:%M:%S").time()
# end = datetime.datetime.strptime('2012-06-21 14:00:00', "%Y-%m-%d %H:%M:%S").time()
#
# # Make up some VWAP vol profiles
# volProfiles = []
# volProfiles.append(VolWindow(datetime.datetime.strptime('2012-06-21 13:30:00', "%Y-%m-%d %H:%M:%S").time(), datetime.datetime.strptime('2012-06-21 13:35:00', "%Y-%m-%d %H:%M:%S").time()))
# volProfiles[0].volProfile = 5
# volProfiles.append(VolWindow(datetime.datetime.strptime('2012-06-21 13:35:00', "%Y-%m-%d %H:%M:%S").time(), datetime.datetime.strptime('2012-06-21 13:40:00', "%Y-%m-%d %H:%M:%S").time()))
# volProfiles[1].volProfile = 5
# volProfiles.append(VolWindow(datetime.datetime.strptime('2012-06-21 13:40:00', "%Y-%m-%d %H:%M:%S").time(), datetime.datetime.strptime('2012-06-21 13:45:00', "%Y-%m-%d %H:%M:%S").time()))
# volProfiles[2].volProfile = 5
# volProfiles.append(VolWindow(datetime.datetime.strptime('2012-06-21 13:45:00', "%Y-%m-%d %H:%M:%S").time(), datetime.datetime.strptime('2012-06-21 13:50:00', "%Y-%m-%d %H:%M:%S").time()))
# volProfiles[3].volProfile = 5
# volProfiles.append(VolWindow(datetime.datetime.strptime('2012-06-21 13:50:00', "%Y-%m-%d %H:%M:%S").time(), datetime.datetime.strptime('2012-06-21 13:55:00', "%Y-%m-%d %H:%M:%S").time()))
# volProfiles[4].volProfile = 5
# volProfiles.append(VolWindow(datetime.datetime.strptime('2012-06-21 13:55:00', "%Y-%m-%d %H:%M:%S").time(), datetime.datetime.strptime('2012-06-21 14:00:00', "%Y-%m-%d %H:%M:%S").time()))
# volProfiles[5].volProfile = 5
#
# # Create a file to write our results to
# f = open('{}/testresultstrading.csv'.format(os.getcwd()), 'w')
#
#
# mornTrading = Trading(True, date, start, end, volProfiles, filename, 585.440000, debugFile=f)
# mornTrading.trade()
#
# # tradeprices = [i for i in mornTrading.trades]
# # times = [i.end for i in volProfiles]
# # pylab.plot_date(times, tradeprices)
# # pylab.plot_date(pylab.date2num(times), tradeprices)
# pylab.show()
