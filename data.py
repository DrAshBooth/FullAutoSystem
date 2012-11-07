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
    if DATAtarget: 
        DATAtargetList.append([])
        DATAtargetList[-1] = [ i for i in DATAtemptargetList]
        DATAtemptargetList[:] = []
    if DATAquote: 
        DATAquoteList.append([])
        DATAquoteList[-1] = [ i for i in DATAtempquoteList]
        DATAtempquoteList[:] = []
    if DATAtrade: 
        DATAtradeList.append([])
        DATAtradeList[-1] = [ i for i in DATAtemptradeList]
        DATAtemptradeList[:] = []
    
    if DATAmyvwap: DATAmyvwapList.append(myvwap)
    if DATAvwap: DATAvwapList.append(vwap)
    if DATAbors: DATAborsList.append(buyorsell)
    
