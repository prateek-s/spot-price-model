fdir<-'~/spot_prices_2015/'
fname<-paste(fdir,'eu-west-1a_cc2.8xlarge_Linux',sep='')
fname

d<-read.csv(fname,header=TRUE,sep=' ')
t<-ts(d)
