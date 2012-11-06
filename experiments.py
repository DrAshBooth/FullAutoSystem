'''
Created on Nov 6, 2012

@author: user
'''

#########################################################
######################## Testing ########################
#########################################################

from vwap import *
from Trading import *

NUM_EXPERIMENTS = 1

dates = [datetime.datetime.strptime('2012-06-21', "%Y-%m-%d"), datetime.datetime.strptime('2012-06-22', "%Y-%m-%d"),
         datetime.datetime.strptime('2012-06-25', "%Y-%m-%d")]
oPrices = [585.440000, 579.210000, 577.300000]
for i in range(NUM_EXPERIMENTS):
    
    date = dates[i]
    filename = os.getcwd() + '/tickData/' + date.strftime('%Y%m%d') + 'AAPL US Equityopen.csv'
    startTrading = datetime.datetime.combine(date, datetime.time(13, 30, 0))    
    # datetime.datetime.strptime('{} 13:30:00'.format(date.strftime('%Y-%m-%d')), "%Y-%m-%d %H:%M:%S").time()
    endTrading = datetime.datetime.combine(date, datetime.time(14, 0, 0))    
    
    # Make up some VWAP vol profiles
    volProfiles = []
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
    
    # Create a file to write our results to
    f = open('{}/testresultstrading.csv'.format(os.getcwd()), 'w')
    
    # trade
    mornTrading = Trading(True, date, startTrading, endTrading, volProfiles, filename, oPrices[i], debugFile=f)
    mornTrading.trade()
    
    # grab results
    myVWAP = mornTrading.WhatsMyVWAP()
    
    # skim through file to work out period VWAP

# average results
# plot results





# tradeprices = [i for i in mornTrading.trades]
# times = [i.end for i in volProfiles]
# pylab.plot_date(times, tradeprices)
# pylab.plot_date(pylab.date2num(times), tradeprices)
pylab.show()
