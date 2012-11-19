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

from operator import attrgetter


BINSIZE = datetime.timedelta(minutes=5)
ticker = "AAPL US Equity"

start_date = datetime.date(2012,6,21)
end_date = datetime.date(2012,6,25)


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
    

class Individual(object):
    
    def __init__(self, genotype):
        self.genotype=genotype
        self.fitness = None

    def assessFitness(self):
        trade_at_open = True
        fitnessess = []
        trading_days , open_prices, buyings = populateTradingDays('AAPL')
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
            trade_prices = trading_session.trades
            
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
    
    def mutateGene(self, original, loci):
        if loci==0: # alpha
            lower_bound=0.0
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
            lower_bound=0.0
            upper_bound=1.0
            new_gene = original + (random.random()/10.-0.05)
            if new_gene<lower_bound: new_gene=lower_bound
            elif new_gene>upper_bound: new_gene=upper_bound
            return new_gene
        elif loci==3: #ThetaMax
            lower_bound=0.0
            upper_bound= 20.0
            new_gene = original + (random.random()*2.-1.0) 
            if new_gene<lower_bound: new_gene=lower_bound
            elif new_gene>upper_bound: new_gene=upper_bound
            return new_gene
        elif loci==4: #ThetaMin
            lower_bound=-20.0
            upper_bound= 0.0
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
            lower_bound=0.0001
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
    
    def createInitialPop(self):
        for i in range(self.pop_size):
            self.population.append(Individual(self.start_genome))

    def assessPopFitness(self):
        fit_sum=0
        for agent in self.population:
            agent.assessFitness()
            fit_sum+=agent.fitness
        self.average_fitness = fit_sum/float(self.pop_size)
        if self.data_on:
            self.file.write("{}, {}\n".format(self.generation,self.average_fitness))
    
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
        
    def evolve(self,generations):
        self.createInitialPop()
        self.assessPopFitness()
        for i in range(generations):
            self.createNewGen()
            self.assessPopFitness()
            print "generation ", self.generation
            self.generation+=1
            
    def writeGeneToFile(self):
        of = open('{}/GAgenotypes.csv'.format(os.getcwd()), 'w')
        for i in self.population:
            of.write(",".join(str(x) for x in i.genotype))
            of.write('\n')
        of.close()
    
#############################################
################# Run It ####################
#############################################


initial_genome = [0.3, 5, 0.3, 5.0, -10.0, 0.02, 0.01, 0.4, 0.4, 2.0, 5, 5.0]

the_pop = Population(initial_genome,10,True)

fitness=[]
time = []

the_pop.evolve(1)
the_pop.writeGeneToFile()

the_pop.file.close()





