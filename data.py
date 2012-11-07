'''
Created on Nov 7, 2012

@author: Ash Booth
'''

# Global Variables for retrieving data, includes switches

#####################
##### Execution #####
#####################

DATAtarget = False
DATAquote = False
DATAtrade = True
DATAvwap = True
DATAmyvwap = True
DATAbors = False

DATAtemptargetList = []
DATAtargetList = []

DATAtempquoteList = []
DATAquoteList = []

DATAtemptradeList = []
DATAtradeList = []

DATAvwapList = []
DATAmyvwapList = []
DATAborsList = []


def endOfSessionDATA(myvwap, vwap, buyorsell):
    DATAtargetList.append(DATAtemptargetList)
    DATAquoteList.append(DATAtempquoteList)
    DATAtradeList.append(DATAtemptradeList)
    DATAtemptargetList = []
    DATAtempquoteList = []
    DATAtemptradeList = []
    
    DATAmyvwapList.append(myvwap)
    DATAvwapList.append(vwap)
    DATAborsList.append(buyorsell)
    
