'''
Created on Nov 12, 2012

@author: Ash Booth
'''
#######################################
############### Imports ###############
#######################################

# Rpy2
import rpy2
from rpy2.robjects.numpy2ri import numpy2ri
import rpy2.robjects as ro
ro.conversion.py2ri = numpy2ri
rpy2.robjects.numpy2ri.activate()
from rpy2.robjects import r

import random
import datetime
from vwap import *
from Trading import *


BINSIZE = datetime.timedelta(minutes=5)
tickers = ["ADBE US Equity"]

start_date = datetime.date(2012,9,1)
end_date = datetime.date(2012,9,10)


def populateTradingDays(ticker):
    r('source("/Users/user/git/FullAutoSystem/oneStockXTS.r")')
    r('setwd("/Users/user/git/FullAutoSystem")')
    
    r.assign('remoteTICKER', ticker.split()[0])
    r.assign('remoteSTART', start_date.strftime('%Y%m%d'))
    r.assign('remoteEND', end_date.strftime('%Y%m%d'))
    r('DB<-getTradingDays(remoteTICKER,remoteSTART,remoteEND)')
    
    # Need to get a vector of datetimes of trading days
    tradingDays = []
    theUTCdates = r('index(DB)')
    floatOpenPrices = r('DB$Open')
    floatClosePrices = r('DB$Close')
    openPrices = []
    directions = []
    
    for (i,date) in enumerate(theUTCdates):
        tradingDays.append(datetime.datetime.fromtimestamp(date))
        if(float(floatClosePrices[i])>=(float(floatOpenPrices[i]))):
            directions.append(True)
        else: directions.append(False)
        openPrices.append(float(floatOpenPrices[i]))
    return tradingDays, openPrices, directions
    

class Individual(object):
    
    def __init__(self, genotype):
        self.alpha = genotype[0]
        self.q_max = genotype[1]
        self.eta = genotype[2]
        self.theta_max = genotype[3]
        self.theta_min = genotype[4]
        self.d_agg_rel = genotype[5]
        self.d_agg_abs = genotype[6]
        self.learn_rate_agg = genotype[7]
        self.learn_rate_theta = genotype[8]
        self.gamma = genotype[9]
        self.smiths_n = genotype[10]
        self.phi = genotype[11]
        
        self.fitness = None

    def mutateAlpha(self,original):
        lower_bound=0.0
        upper_bound=1.0
        new_gene = original + (random.random()/10.-0.05)
        if new_gene<lower_bound: new_gene=lower_bound
        elif new_gene>upper_bound: new_gene=upper_bound
        return new_gene
        
    def mutateQmax(self, original):
        lower_bound=1
        upper_bound=60
        new_gene = original+(random.randint(0,6)-3)
        if new_gene<lower_bound: new_gene=lower_bound
        elif new_gene>upper_bound: new_gene=upper_bound
        return new_gene
    
    def mutateEta(self,original):
        lower_bound=0.0
        upper_bound=1.0
        new_gene = original + (random.random()/10.-0.05)
        if new_gene<lower_bound: new_gene=lower_bound
        elif new_gene>upper_bound: new_gene=upper_bound
        return new_gene
    
    def mutateThetaMax(self, original):
        lower_bound=0.0
        upper_bound= 20.0
        new_gene = original + (random.random()*2.-1.0) 
        if new_gene<lower_bound: new_gene=lower_bound
        elif new_gene>upper_bound: new_gene=upper_bound
        return new_gene
    
    def mutateThetaMin(self, original):
        lower_bound=-20.0
        upper_bound= 0.0
        new_gene = original + (random.random()*2.-1.0) 
        if new_gene<lower_bound: new_gene=lower_bound
        elif new_gene>upper_bound: new_gene=upper_bound
        return new_gene
        
    def mutatedAggRel(self,original):
        lower_bound=0.0
        upper_bound=1.0
        new_gene = original + (random.random()/10.-0.05)
        if new_gene<lower_bound: new_gene=lower_bound
        elif new_gene>upper_bound: new_gene=upper_bound
        return new_gene
        
    def mutatedAggAbs(self,original):
        lower_bound=0.0
        upper_bound=1.0
        new_gene = original + (random.random()/10.-0.05)
        if new_gene<lower_bound: new_gene=lower_bound
        elif new_gene>upper_bound: new_gene=upper_bound
        return new_gene
    
    def mutateLearnRateAgg(self,original):
        lower_bound=0.0
        upper_bound=1.0
        new_gene = original + (random.random()/10.-0.05)
        if new_gene<lower_bound: new_gene=lower_bound
        elif new_gene>upper_bound: new_gene=upper_bound
        return new_gene
    
    def mutateLearnRateTheta(self,original):
        lower_bound=0.0
        upper_bound=1.0
        new_gene = original + (random.random()/10.-0.05)
        if new_gene<lower_bound: new_gene=lower_bound
        elif new_gene>upper_bound: new_gene=upper_bound
        return new_gene
    
    def mutateGamma(self,original):
        lower_bound=0.0001
        upper_bound=5.0
        new_gene = original + (random.random()/2.-0.25)
        if new_gene<lower_bound: new_gene=lower_bound
        elif new_gene>upper_bound: new_gene=upper_bound
        return new_gene

    def assessFitness(self):
        trade_at_open = True
        fitnessess = []
        trading_days , open_prices, buyings = populateTradingDays('AAPL')
        for ticker in tickers:
            for (d,date) in enumerate(trading_days):
                # Make up some VWAP vol profiles
                buying = buyings[d]
                volProfiles = []
                if trade_at_open: 
                    filename = os.getcwd() + '/tickData/' + date.strftime('%Y%m%d') + ticker + 'open.csv'
                    startTrading = datetime.datetime.combine(date, datetime.time(13, 30, 0))    
                    endTrading = datetime.datetime.combine(date, datetime.time(14, 0, 0))  
                    volProfiles.append(VolWindow(datetime.time(13, 30, 0), datetime.time(13, 35, 0)))
                    volProfiles[0].volProfile = 5 
                    volProfiles.append(VolWindow(datetime.time(13, 35, 0), datetime.time(13, 40, 0)))
                    volProfiles[1].volProfile = 5
                    volProfiles.append(VolWindow(datetime.time(13, 40, 0), datetime.time(13, 45, 0)))
                    volProfiles[2].volProfile = 5
                    volProfiles.append(VolWindow(datetime.time(13, 45, 0), datetime.time(13, 50, 0)))
                    volProfiles[3].volProfile = 5
                    volProfiles.append(VolWindow(datetime.time(13, 50, 0), datetime.time(13, 55, 0)))
                    volProfiles[4].volProfile = 5
                    volProfiles.append(VolWindow(datetime.time(13, 55, 0), datetime.time(14, 00, 0)))
                    volProfiles[5].volProfile = 5
                else:
                    filename = os.getcwd() + '/tickData/' + date.strftime('%Y%m%d') + ticker + 'close.csv'
                    startTrading = datetime.datetime.combine(date, datetime.time(13, 30, 0))    
                    endTrading = datetime.datetime.combine(date, datetime.time(14, 0, 0))  
                    volProfiles.append(VolWindow(datetime.time(13, 30, 0), datetime.time(13, 35, 0)))
                    volProfiles[0].volProfile = 5 
                    volProfiles.append(VolWindow(datetime.time(13, 35, 0), datetime.time(13, 40, 0)))
                    volProfiles[1].volProfile = 5
                    volProfiles.append(VolWindow(datetime.time(13, 40, 0), datetime.time(13, 45, 0)))
                    volProfiles[2].volProfile = 5
                    volProfiles.append(VolWindow(datetime.time(13, 45, 0), datetime.time(13, 50, 0)))
                    volProfiles[3].volProfile = 5
                    volProfiles.append(VolWindow(datetime.time(13, 50, 0), datetime.time(13, 55, 0)))
                    volProfiles[4].volProfile = 5
                    volProfiles.append(VolWindow(datetime.time(13, 55, 0), datetime.time(14, 00, 0)))
                    volProfiles[5].volProfile = 5
                
                theVWAP = VWAP(startTrading.time(),endTrading.time(),BINSIZE)
                trading_session = Trading(buying, date, startTrading, endTrading, 
                                          volProfiles, filename, open_prices[d], self.genotype)
                trading_session.trade()
                trade_prices = trading_session.trades
                
                theVWAP.addDatapointFile(filename, False)
                the_vwaps = theVWAP.getBinVWAPS()
                
                for (i,price) in enumerate(trade_prices):
                    if price==None:
                        fitnessess.append(0.0)
                    else:
                        if buying: f = (the_vwaps[i]-price)/float(the_vwaps[i])
                        else: f = (price-the_vwaps[i])/float(the_vwaps[i])
                        fitnessess.append(1+f)
    
        return (sum(fitnessess)/float(len(fitnessess)))
    
    def mutateGene(self, original_gene):
        MUTATIONFACTOR = 0.05
        if isinstance(original_gene,int):
            
            
        else:
            




