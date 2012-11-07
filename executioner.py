'''
Created on 7 Sep 2012

@author: Ash Booth

As input takes order direction (buy or sell)
and list of vol windows (contain times, sizes, 
etc).
Executes trade with volatility adaptive algo.

'''
import math
from parameters import *
from dates import *

class Quote(object):
    def __init__(self, time, buying, price, vol):
        self.buying = buying
        self.price = price
        self.vol = vol
        self.born = time

class Executioner(object):
    '''
    classdocs
    '''


    def __init__(self, date, time, buying, start, end, volume, start_eqlbm, startBB, startBA, mmax,
                 theta, limit , target, smithsAlpha, agg):
        '''
        Constructor
        '''
        self.date = date
        self.time = time
        
        self.start = start
        self.end = end
        self.buying = buying
        self.notTraded = True
        self.salePrice = None
        self.sleepTime = 20
        
        self.eqlbm = start_eqlbm
        self.eqlbm_alpha = 0.3
        self.marketMax = mmax
        
        self.currentBid = startBB
        self.currentAsk = startBA
        self.submittedTrade = False
        self.myquote = None
        
        self.maxQuoteLife = datetime.timedelta(seconds=5)
        self.nu = 3.0
        self.currentTradeSize = None
        
        self.volume = volume
        self.lastTrades = []
        self.nLastTrades = 5
        
        self.theta = theta
        self.thetaMax = 2
        self.thetaMin = -8
        self.limit = limit
        self.aggressiveness = agg
        
        self.target = target
        self.dAggAbs = 0.01
        self.dAggRel = 0.02
        self.learnRateAgg = 0.4
        self.learnRateTheta = 0.4
        self.smithsAlpha = smithsAlpha
        self.smithsAlphaMin = 0.099
        self.smithsAlphaMax = 0.101
        self.gamma = 2.0
        
        self.maxNewtonItter = 10
        self.maxNewtonError = 0.0001


    def updateEq(self, price):
        self.eqlbm = self.eqlbm_alpha * price + (1 - self.eqlbm_alpha) * self.eqlbm
        
    def newton4Buying(self):
        theta_est = self.theta
        rightHside = ((self.theta * (self.limit - self.eqlbm)) / float(math.exp(self.theta) - 1));
        i = 0
        while i <= self.maxNewtonItter:
            eX = math.exp(theta_est)
            eXminOne = eX - 1
            fofX = (((theta_est * self.eqlbm) / float(eXminOne)) - rightHside)
            if abs(fofX) <= self.maxNewtonError:
                break
            dfofX = ((self.eqlbm / eXminOne) - ((eX * self.eqlbm * theta_est) / float(eXminOne * eXminOne)))
            theta_est = (theta_est - (fofX / float(dfofX)));
            i += 1
        if theta_est == 0.0: theta_est += 0.000001
        return theta_est
    
    def newton4Selling(self):
        theta_est = self.theta
        rightHside = ((self.theta * (self.eqlbm - self.limit)) / float(math.exp(self.theta) - 1))
        i = 0
        while i <= self.maxNewtonItter:
            eX = math.exp(theta_est)
            eXminOne = eX - 1
            fofX = (((theta_est * (self.marketMax - self.eqlbm)) / float(eXminOne)) - rightHside)
            if abs(fofX) <= self.maxNewtonError:
                break
            dfofX = (((self.marketMax - self.eqlbm) / eXminOne) - ((eX * (self.marketMax - self.eqlbm) * theta_est) / float(eXminOne * eXminOne)))
            theta_est = (theta_est - (fofX / float(dfofX)))
            i += 1
        if theta_est == 0.0: theta_est += 0.000001
        return theta_est
        
    def updateTarget(self):
        if self.buying:
            if self.limit < self.eqlbm:
                # Extra-marginal buyer
                if self.aggressiveness >= 0: target = self.limit
                else: target = self.limit * (1 - (math.exp(-self.aggressiveness * self.theta) - 1) / float(math.exp(self.theta) - 1))
                self.target = target
            else:
                # Intra-marginal buyer
                if self.aggressiveness >= 0: target = (self.eqlbm + (self.limit - self.eqlbm) * ((math.exp(self.aggressiveness * self.theta) - 1) / float(math.exp(self.theta) - 1)))
                else:
                    theta_est = self.newton4Buying()
                    target = self.eqlbm * (1 - (math.exp(-self.aggressiveness * theta_est) - 1) / float(math.exp(theta_est) - 1))
                self.target = target
        else:
            if self.limit > self.eqlbm:
                # Extra-marginal seller
                if self.aggressiveness >= 0: target = self.limit
                else: target = self.limit + (self.marketMax - self.limit) * ((math.exp(-self.aggressiveness * self.theta) - 1) / float(math.exp(self.theta) - 1))
                self.target = target
            else:
                # Intra-marginal seller
                if self.aggressiveness >= 0: target = self.limit + (self.eqlbm - self.limit) * (1 - (math.exp(self.aggressiveness * self.theta) - 1) / float(math.exp(self.theta) - 1))
                else:
                    theta_est = self.newton4Selling() 
                    target = self.eqlbm + (self.marketMax - self.eqlbm) * ((math.exp(-self.aggressiveness * theta_est) - 1) / (math.exp(theta_est) - 1))
                self.target = target
        if DATAtarget: DATAtemptargetList.append(self.target)
    
    def calcRshout(self, target):
        # target must be:
        #    - highest bid if last was bid
        #    - lowest ask if last was ask
        #    - trade price if last was trade
        if self.buying:
            # Are we extramarginal?
            if self.eqlbm >= self.limit:
                r_shout = 0.0
            else:  # Intra-marginal
                if target > self.eqlbm:
                    if target > self.limit: target = self.limit
                    r_shout = math.log((((target - self.eqlbm) * (math.exp(self.theta) - 1)) / (self.limit - self.eqlbm)) + 1) / self.theta
                else:  # other formula for intra buyer
                    r_shout = math.log((1 - (target / self.eqlbm)) * (math.exp(self.newton4Buying()) - 1) + 1) / -self.newton4Buying()
        else:  # Selling
            # Are we extra-marginal?
            if self.limit >= self.eqlbm:
                r_shout = 0.0
            else:  # Intra-marginal
                if target > self.eqlbm:
                    r_shout = math.log(((target - self.eqlbm) * (math.exp(self.newton4Selling()) - 1)) / (self.marketMax - self.eqlbm) + 1) / -self.newton4Selling()
                else:  # other intra seller formula
                    if target < self.limit: target = self.limit
                    r_shout = math.log((1 - (target - self.limit) / (self.eqlbm - self.limit)) * (math.exp(self.theta) - 1) + 1) / self.theta
        return r_shout
    
    def updateAgg(self, up, target):
        if up:
            delta = (1 + self.dAggRel) * self.calcRshout(target) + self.dAggAbs
        else:
            delta = (1 - self.dAggRel) * self.calcRshout(target) - self.dAggAbs
        self.aggressiveness = self.aggressiveness + self.learnRateAgg * (delta - self.aggressiveness)
    
    def updateSalpha(self, price):
        self.lastTrades.append(price)
        if not (len(self.lastTrades) < self.nLastTrades): self.lastTrades.pop(0)
        self.smithsAlpha = math.sqrt(sum(((p - self.eqlbm) ** 2) for p in self.lastTrades) * (1 / float(len(self.lastTrades)))) / self.eqlbm
        if self.smithsAlpha < self.smithsAlphaMin: self.smithsAlphaMin = self.smithsAlpha
        if self.smithsAlpha > self.smithsAlphaMax: self.smithsAlphaMax = self.smithsAlpha
    
    def updateTheta(self):
        alphaBar = (self.smithsAlpha - self.smithsAlphaMin) / (self.smithsAlphaMax - self.smithsAlphaMin)
        desiredTheta = (self.thetaMax - self.thetaMin) * (1 - (alphaBar * math.exp(self.gamma * (alphaBar - 1)))) + self.thetaMin
        theta = self.theta + self.learnRateTheta * (desiredTheta - self.theta)
        if theta == 0: theta += 0.0000001
        self.theta = theta
        
    def submitQuote(self):
        if self.buying:
            price = (self.currentBid + (self.target - self.currentBid) / self.nu)
            self.myquote = Quote(self.time, True, price, self.volume)
            self.submittedTrade = True
        else: 
            price = (self.currentAsk - (self.currentAsk - self.target) / self.nu)
            self.myquote = Quote(self.time, False, price, self.volume)

            self.submittedTrade = True
        if DATAquote: DATAtempquoteList.append(price)
                    
    def checkForClearing(self, price):
        if self.buying and (price <= self.myquote.price):
            self.salePrice = price
            self.notTraded = False
            if DATAtrade:
                DATAtemptradeList.append(price)
        elif (not self.buying) and (price >= self.myquote.price):
            self.salePrice = price
            self.notTraded = False
            if DATAtrade:
                DATAtemptradeList.append(price)
            
    def getTradeResults(self):
            return self.salePrice
        
    def newInfo(self, time, price, trade, bid):
        self.time = time
        if self.sleepTime > 0:
            self.sleepTime -= 1
        if trade:
            self.updateEq(price)
            self.updateSalpha(price)
            self.updateTheta()
        else:
            if bid: self.currentBid = price
            else: self.currentAsk = price

        if self.buying:
            if trade:
                if self.target >= price: 
                    self.updateAgg(False, price)
                else: self.updateAgg(True, price)
            elif FULLBOOK: 
                if bid and (self.target <= price): self.updateAgg(True, self.currentBid)
        else:  # selling
            if trade:
                if self.target <= price:  self.updateAgg(False, price)
                else: self.updateAgg(True, price)
            elif FULLBOOK:
                if (not bid) and (self.target >= price): self.updateAgg(True, self.currentAsk)
        self.updateTarget()
        # Do I still need to trade?
        if self.notTraded:
            # If I've submitted a quote let's see if it's expired or if it clears
            if self.submittedTrade:
                if time > (datetime.datetime.combine(self.date, self.myquote.born) + self.maxQuoteLife).time():
                    # cancel old and submit new quote
                    self.submitQuote()
                # Will it clear?
                if trade:
                    self.checkForClearing(price)
            # If wait time is over and I am yet to submit a quote - submit one
            elif (self.sleepTime <= 0):
                self.submitQuote()
