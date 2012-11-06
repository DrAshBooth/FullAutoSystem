# Plotting tick data

library(xts)

# Read the data file
tickData<-read.csv("20120621AAPL US Equityopen.csv",header=F)

# Separate bids, asks and trades
bids<-tickData[tickData[2]=='BEST_BID',]
asks<-tickData[tickData[2]=='BEST_ASK',]
trades<-tickData[tickData[2]=='TRADE',]

# Turn the data frames into extensible time series
bidsxts<-xts(bids[,-1],order.by=strptime(bids[,1], "%Y-%m-%d %H:%M:%S"))
asksxts<-xts(asks[,-1],order.by=strptime(asks[,1], "%Y-%m-%d %H:%M:%S"))
tradesxts<-xts(trades[,-1],order.by=strptime(trades[,1], "%Y-%m-%d %H:%M:%S"))

plot.xts(bidsxts[,2])
lines(asksxts[,2],col='red')

# Add my trades to plot
MYTRADES<-read.csv('testresultstrading.csv',header=F)
MYTRADESxts<-xts(MYTRADES[,-1],order.by=strptime(MYTRADES[,1], "%Y-%m-%d %H:%M:%S"))
points(MYTRADESxts[,1],col='blue',pch=16, cex=2)
