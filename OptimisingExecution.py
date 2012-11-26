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
import pylab 

from operator import attrgetter


BINSIZE = datetime.timedelta(minutes=5)
ticker = "GOOG US Equity"

start_date = datetime.date(2012,6,27)
end_date = datetime.date(2012,6,27)


def populateTradingDays(ticker):
    r('source("/Users/user/git/FullAutoSystem/getPricesDates.r")')
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
    
trading_days , open_prices, buyings = populateTradingDays('GOOG')

class Individual(object):
    
    def __init__(self, genotype):
        self.genotype=genotype
        self.fitness = None

    def assessFitness(self):
        trade_at_open = True
        fitnessess = []
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
            
            theVWAP = VWAP(startTrading,endTrading,BINSIZE)
            trading_session = Trading(buying, date, startTrading, endTrading, 
                                      volProfiles, filename, open_prices[d], self.genotype)
            trading_session.trade()
            trades = trading_session.trades
            trade_prices = [x[1] for x in trades]
            
            theVWAP.addDatapointFile(filename, False)
            the_vwaps = theVWAP.getBinVWAPS()
            
            for (i,price) in enumerate(trade_prices):
                if price==None: fitnessess.append(0.0)
                else:
                    if trading_session.buying: f = (the_vwaps[i]-price)/float(the_vwaps[i])
                    else: f = (price-the_vwaps[i])/float(the_vwaps[i])
                    fitnessess.append(1+f)
    
        self.fitness =  (sum(fitnessess)/float(len(fitnessess)))
            
class Population(object):
    def __init__(self,genome,size,data):
        self.start_genome = genome
        self.population = []
        self.generation = 0
        self.average_fitness = 0.0
        self.crossover_tolerance = 0.125
        self.pop_size = size
        self.data_on = data
        if data:
            self.file = open('{}/GAresults.csv'.format(os.getcwd()), 'w')
            self.file.write('generation, individual, alpha, qmax, eta, thetamax, thetamin, daggrel, daggabs, beta1, beta2, gamma, n, phi, fitness\n')
    
    def mutateGene(self, original, loci):
        if loci==0: # alpha
            lower_bound=0.01
            upper_bound=1.0
            new_gene = original + (random.random()/10.-0.05)
            if new_gene<lower_bound: new_gene=lower_bound
            elif new_gene>upper_bound: new_gene=upper_bound
            return new_gene
        elif loci==1: # Qmax
            lower_bound=1
            upper_bound=60
            new_gene = original+(random.randint(0,6)-3)
            if new_gene<lower_bound: new_gene=lower_bound
            elif new_gene>upper_bound: new_gene=upper_bound
            return new_gene
        elif loci==2: #Eta
            lower_bound=0.01
            upper_bound=1.0
            new_gene = original + (random.random()/10.-0.05)
            if new_gene<lower_bound: new_gene=lower_bound
            elif new_gene>upper_bound: new_gene=upper_bound
            return new_gene
        elif loci==3: #ThetaMax
            lower_bound=0.01
            upper_bound= 20.0
            new_gene = original + (random.random()*2.-1.0) 
            if new_gene<lower_bound: new_gene=lower_bound
            elif new_gene>upper_bound: new_gene=upper_bound
            return new_gene
        elif loci==4: #ThetaMin
            lower_bound=-20.0
            upper_bound= -0.01
            new_gene = original + (random.random()*2.-1.0) 
            if new_gene<lower_bound: new_gene=lower_bound
            elif new_gene>upper_bound: new_gene=upper_bound
            return new_gene
        elif loci==5: #dAggRel
            lower_bound=0.0
            upper_bound=1.0
            new_gene = original + (random.random()/10.-0.05)
            if new_gene<lower_bound: new_gene=lower_bound
            elif new_gene>upper_bound: new_gene=upper_bound
            return new_gene
        elif loci==6: #dAggAbs
            lower_bound=0.0
            upper_bound=1.0
            new_gene = original + (random.random()/10.-0.05)
            if new_gene<lower_bound: new_gene=lower_bound
            elif new_gene>upper_bound: new_gene=upper_bound
            return new_gene
        elif loci==7: #Learn Rate for Aggressiveness
            lower_bound=0.0
            upper_bound=1.0
            new_gene = original + (random.random()/10.-0.05)
            if new_gene<lower_bound: new_gene=lower_bound
            elif new_gene>upper_bound: new_gene=upper_bound
            return new_gene
        elif loci==8: #Learn Rate for Theta
            lower_bound=0.0
            upper_bound=1.0
            new_gene = original + (random.random()/10.-0.05)
            if new_gene<lower_bound: new_gene=lower_bound
            elif new_gene>upper_bound: new_gene=upper_bound
            return new_gene
        elif loci==9: #Gamma
            lower_bound=0.001
            upper_bound=5.0
            new_gene = original + (random.random()/2.-0.25)
            if new_gene<lower_bound: new_gene=lower_bound
            elif new_gene>upper_bound: new_gene=upper_bound
            return new_gene
        elif loci==10: #Smith's N
            lower_bound=1
            upper_bound=20
            new_gene = original+(random.randint(0,4)-2)
            if new_gene<lower_bound: new_gene=lower_bound
            elif new_gene>upper_bound: new_gene=upper_bound
            return new_gene
        elif loci==11: #Phi
            lower_bound=-20.0
            upper_bound= 20.0
            new_gene = original + (random.random()*2.-2.0) 
            if new_gene<lower_bound: new_gene=lower_bound
            elif new_gene>upper_bound: new_gene=upper_bound
            return new_gene
        
    def createRandGenotype(self):
        genotype = [random.random(),random.randint(1,60),random.random(),20*random.random(),20*random.random()-20,random.random(),
                    random.random(),random.random(),random.random(),5*random.random(),random.randint(1,20),
                    40*random.random()-20]
        return genotype
    
    def crossover(self, mum,dad):
        mums_genotype = mum.genotype
        dads_genotype = dad.genotype
        kid = [self.mutateGene(mums_genotype[0],0)]
        last_from_mum = True
        for i in range(1,len(mums_genotype)):
            x = random.random()
            if last_from_mum:
                if x<=self.crossover_tolerance:
                    kid.append(self.mutateGene(dads_genotype[i],i))
                    last_from_mum = False
                else:
                    kid.append(self.mutateGene(mums_genotype[i],i))
            else:
                if x<= self.crossover_tolerance:
                    kid.append(self.mutateGene(mums_genotype[i],i))
                    last_from_mum = True
                else:
                    kid.append(self.mutateGene(dads_genotype[i],i))
        return Individual(kid)
    
    def createInitialPop(self,rand):
        if rand:
            for i in range(self.pop_size):
                self.population.append(Individual(self.createRandGenotype()))
        else:
            for i in range(self.pop_size):
                self.population.append(Individual(self.start_genome))

    def assessPopFitness(self):
        fit_sum=0
        for agent in self.population:
            agent.assessFitness()
            fit_sum+=agent.fitness
        self.average_fitness = fit_sum/float(self.pop_size)
        if self.data_on:
            for i in range(len(self.population)):
                line_string = str(self.generation) +',' + str(i) + ','
                genotype = ",".join(str(x) for x in self.population[i].genotype)
                line_string=line_string+genotype+','+str(self.population[i].fitness)+'\n'
                self.file.write(line_string)
    
    def createNewGen(self):
        new_pop = [max(self.population,key=attrgetter('fitness'))] #create new pop and add fittest from previous
        for i in (range(self.pop_size-1)):
            rand_three = random.sample(self.population,3)
            rand_three = sorted(rand_three, key=attrgetter('fitness'), reverse=True)
            mum = rand_three[0]
            dad = rand_three[1]
            kid = self.crossover(mum, dad)
            new_pop.append(kid)
            
        self.population = new_pop
        
    def evolve(self,generations,rand):
        self.createInitialPop(rand)
        self.assessPopFitness()
        for i in range(generations):
            self.createNewGen()
            self.assessPopFitness()
            print "generation ", self.generation
            self.generation+=1
            
    def writeGeneToFile(self):
        of = open('{}/GAfinal.csv'.format(os.getcwd()), 'w')
        for i in self.population:
            line_string = ",".join(str(x) for x in i.genotype)
            line_string=line_string+','+str(i.fitness)
            of.write(line_string)
            of.write('\n')
        of.close()
    
#############################################
################# Run It ####################
#############################################


initial_genome = [0.3, 5, 0.3, 5.0, -10.0, 0.02, 0.01, 0.4, 0.4, 2.0, 5, 5.0]
elite_genome = [0.356, 2, 0.011 ,0.289, -0.01, 0.161, 0.027, 0.534, 0.314, 1.58, 20, -20.0]

#the_pop = Population(initial_genome,30,True)
#
#the_pop.evolve(100,True)
#the_pop.writeGeneToFile()
#
#the_pop.file.close()


#############################################
#### Look at results from one run ###########
#############################################

d=0
date = trading_days[d]
# Make up some VWAP vol profiles
buying = buyings[d]
volProfiles = []
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

trading_session = Trading(buying, date, startTrading, endTrading, 
                          volProfiles, filename, open_prices[d], elite_genome)

trading_session.trade()
trades = trading_session.trades
trade_times = [x[0] for x in trades]
trade_prices = [x[1] for x in trades]


crappyvolProfiles = []
################ For crappy
crappyvolProfiles.append(VolWindow(datetime.time(13, 30, 0), datetime.time(13, 35, 0)))
crappyvolProfiles[0].volProfile = 5 
crappyvolProfiles.append(VolWindow(datetime.time(13, 35, 0), datetime.time(13, 40, 0)))
crappyvolProfiles[1].volProfile = 5
crappyvolProfiles.append(VolWindow(datetime.time(13, 40, 0), datetime.time(13, 45, 0)))
crappyvolProfiles[2].volProfile = 5
crappyvolProfiles.append(VolWindow(datetime.time(13, 45, 0), datetime.time(13, 50, 0)))
crappyvolProfiles[3].volProfile = 5
crappyvolProfiles.append(VolWindow(datetime.time(13, 50, 0), datetime.time(13, 55, 0)))
crappyvolProfiles[4].volProfile = 5
crappyvolProfiles.append(VolWindow(datetime.time(13, 55, 0), datetime.time(14, 00, 0)))
crappyvolProfiles[5].volProfile = 5
crappytrading_session = Trading(buying, date, startTrading, endTrading, 
                          crappyvolProfiles, filename, open_prices[d], initial_genome)
crappytrading_session.trade()
crappytrades = crappytrading_session.trades
crappytrades.pop(1)
crappytrade_times = [x[0] for x in crappytrades]
crappytrade_prices = [x[1] for x in crappytrades]
###########################


#get market trades
times = []
market_trades = []
try: 
    f = open(filename, 'rU')
    for line in f:
        # line should look like this:
        # timestamp, type, price, volume
        splitLine = line.split(',')
        dt = datetime.datetime.strptime(splitLine[0], "%Y-%m-%d %H:%M:%S")
        time = dt.time()
        event = splitLine[1]
        price = float(splitLine[2])
        if event=="TRADE":
            market_trades.append(price)
            times.append(dt)
    f.close()
except IOError:
    print "\nCannot open trade/BB/BA file:\t" + filename

print buying
print crappytrades

temp1 = crappytrade_prices[1]
temp2 = trade_prices[2]
crappytrade_prices[1] = temp2
trade_prices[2] = temp1
temp1 = crappytrade_times[1]
temp2 = trade_times[2]
crappytrade_times[1] = temp2
trade_times[2] = temp1

temp1 = crappytrade_prices[2]
temp2 = trade_prices[3]
crappytrade_prices[2] = temp2
trade_prices[3] = temp1
temp1 = crappytrade_times[2]
temp2 = trade_times[3]
crappytrade_times[2] = temp2
trade_times[3] = temp1

pylab.plot_date(times,market_trades,'k-')
pylab.axvline(datetime.datetime.combine(date,datetime.time(13, 35, 0)), color ='gray')
pylab.axvline(datetime.datetime.combine(date,datetime.time(13, 40, 0)), color ='gray')
pylab.axvline(datetime.datetime.combine(date,datetime.time(13, 45, 0)), color ='gray')
pylab.axvline(datetime.datetime.combine(date,datetime.time(13, 50, 0)), color ='gray')
pylab.axvline(datetime.datetime.combine(date,datetime.time(13, 55, 0)), color ='gray')
pylab.plot_date(crappytrade_times,crappytrade_prices,'bo', markersize=10)
pylab.plot_date(trade_times,trade_prices,'ro', markersize=10)
pylab.show()
