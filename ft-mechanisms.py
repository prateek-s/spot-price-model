import os,sys,matplotlib,pandas,numpy,scipy,dateutil
import pandas as pd
import numpy as np
from pylab import *
from datetime import datetime, timedelta
import time
from statsmodels.distributions.empirical_distribution import ECDF
import sqlite3
import itertools, random



#############################################################################              
    
def avail(prices):
    return ECDF(zip(*prices)[1])
        
#############################################################################    
#prices is [(t,p)]    
def expected_cost(bidrange, prices):
    EC=[]
    for b in bidrange:
        avg_under_bid = np.mean(filter(lambda x: x <= b, zip(*prices)[1]))
        EC.append((b,avg_under_bid))

    return EC
  
  
#############################################################################
  
def get_MTTF(bidrange, prices):
    mttfs=[]
    for b in bidrange:
         mttfat = np.mean(get_failures(prices, b))
         #filter >3600.0 here
         #also, 0 => say 1000*3600.0
         if mttfat == 0 or math.isnan(mttfat):
             mttfat = 500*3600.0
         mttfs.append((b, mttfat))
    if mttfs == []:
        mttfs = zip(bidrange, [500*3600.0]*len(bidrange))
    return mttfs

def get_failures(pricetrace, bid, timebuf=3600):
    #Input: [(unixtime, price)]
    #Output: [inter-arrival-times]
    out = []
    firstfail = True
    prevfail = 0
    #Sort the pricetrace first!
    pricetrace = sorted(pricetrace, key=lambda x: x[0])
    for (t,p) in pricetrace:
        if p > bid :
            if firstfail:
                prevfail = t
                firstfail = False
            else :
                iat = t - prevfail
                prevfail = t
                if iat < timebuf:
                    #ignore it, do not append!
                    pass
                else:
                    out.append(iat)

    #print "Number of failures: "+str(len(out))
    return out       

############################################################################


######################################################################

NPavail = []
NPcost = []
#Given a bid, find the closest corresponding availability.  The avail
#array might not be indexed by the same bids because it is generated
#by ECDF function.

def resample_cdf(cdf, bids):
    NPavail = np.array(cdf)
    newcdf = []
    for b in bids :
        idx = find_nearest_idx(NPavail[:,0], b)
        avail = NPavail[idx, 1]
        newcdf.append((b,avail))
        
    return newcdf

def mk_avail_array(data):
    global NPavail
    NPavail = np.array(data)

def mk_cost_array(data):
    global NPcost
    NPcost = np.array(data)

def find_nearest_idx(array, value):
    idx = (np.abs(array-value)).argmin()
    return idx

#Given a bid, find the closest corresponding availability.  The avail
#array might not be indexed by the same bids because it is generated
#by ECDF function.
def avail_at_bid(b, avail):
    global NPavail
    idx = find_nearest_idx(NPavail[:,0], b)
    g = NPavail[idx,1]
    return float(g)

def cost_at_bid(b, cost):
    global NPcost
    idx = find_nearest_idx(NPcost[:,0], b)
    g = NPcost[idx,1]
    return float(g)

#####################################################################




######################################################################
#Everything is normalized to ondemand, dont forget!
# b,cost
def no_ft(avail, cost, mttf):
    #[(b, cost)]
    return cost 

#Get revoked with some probability. Then double
def restart(avail, cost, mttf):
    result = []
    for (b, c) in cost:
        p = avail_at_bid(b, avail)
        ec = c*p + (1-p)*2*c
        result.append((b, ec))

    return result

#Complex tau formula. Recheck!
def ckpt(avail, cost, mttf):
    result = []
    delta = 120.0/3600.0 #in hours!
    for (b, m) in mttf:
        tau = math.sqrt(2*delta*m/3600.0)
        t = 1.0 + (delta/tau) + (tau/2*m)
        c = cost_at_bid(b, cost)
        ec = float(c)*t

        result.append((b, ec))

    return result

#Similar to restart
def migrate(avail, cost, mttf):
    result = []
    for (b, c) in cost:
        p = avail_at_bid(b, avail)
        ec = c*p + (1-p)
        result.append((b, ec))

    return result
        
######################################################################


def parse_lines(lines):
    #Input: list of strings
    #Input Format: 2012-09-11 09:41:13,0.106
    #Output:list of [(unix-time-seconds, price)]
    pricetrace = []
    for aline in lines:
        #parsing exceptions and all that?
        try:
            #New format is apparently space separated!"
            (tstamp,price) = tuple(aline.split(" "))
            price = float(price)
            dt = dateutil.parser.parse(tstamp)
            tstamp = time.mktime(dt.timetuple())
            pricetrace.append((tstamp, price))
        except Exception:
            print "Exception during parsing: " + aline
            pass
    return pricetrace


######################################################################

if __name__ == '__main__':
    pass
