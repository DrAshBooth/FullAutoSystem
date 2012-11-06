'''
Created on 15 Aug 2012

@author: Ash Booth
'''

import datetime
from parameters import *

def dateRange(start_date, end_date):
    for n in range(int ((end_date - start_date).days)):
        yield start_date + datetime.timedelta(n)
        
def timeRange(start_time, end_time, winSize):
    """
    muse use minutes!
    """
    mins = 0
    for n in range(int ((end_time - start_time).seconds / 60)):
        if mins % (winSize.seconds / 60) == 0:
            yield start_time + datetime.timedelta(minutes=n)
        mins += 1
        
        
divtdi = datetime.timedelta.__div__
def divtd(td1, td2):
    if isinstance(td2, (int, long)):
        return divtdi(td1, td2)
    us1 = td1.microseconds + 1000000 * (td1.seconds + 86400 * td1.days)
    us2 = td2.microseconds + 1000000 * (td2.seconds + 86400 * td2.days) 
    return us1 / us2  # this does integer division, use float(us1) / us2 for fp division

STARTDATE = datetime.date(2008, 01, 01)
DAYS = 400
test_duration = datetime.timedelta(days=DAYS)
ENDDATE = STARTDATE + test_duration

# window needs to account for non-trading days
# i.e. in 150 days, market is probably only active for 90
training_window = datetime.timedelta(days=151)
lag_date = datetime.timedelta(days=(LONGLAG + 365))
one_day = datetime.timedelta(days=1)


# Times for VWAP stuff
MARKETOPEN = datetime.datetime.strptime('19/09/2012  14:30:00', "%d/%m/%Y %H:%M:%S")
MARKETOPEN = MARKETOPEN.time()
MARKETCLOSE = datetime.datetime.strptime('19/09/2012  15:00:00', "%d/%m/%Y %H:%M:%S")
MARKETCLOSE = MARKETCLOSE.time()
WINSIZE = datetime.timedelta(minutes=30)
BINSIZE = datetime.timedelta(minutes=5)

