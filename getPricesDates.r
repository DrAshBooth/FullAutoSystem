library(fTrading)
library(TTR)
library(fGarch)

getTradingDays <- function(ticker,START,END) {
	assetData<-getYahooData(ticker,START,END,freq="daily",adjust=TRUE)
}