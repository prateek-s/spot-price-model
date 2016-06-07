# -*- coding: utf-8 -*-
"""
Created on Thu Feb 25 08:44:04 2016

@author: prateeks
"""

import os,sys,matplotlib,pandas,numpy,scipy,dateutil
import pandas as pd
import numpy as np
from pylab import *
from datetime import datetime, timedelta
import time
from statsmodels.distributions.empirical_distribution import ECDF
import sqlite3
import itertools, random

conn = None

#good months: 5,6,7,8, 10
#bad months : 9 (only 4 days)

def init_db_connection() :
    global conn
    conn = sqlite3.connect('/home/prateeks/spot_prices_2015/aws.db')


def read_data_sqlite(instance , mktstring=None, months=['201503','201504','201505','201506','201507','201508']):
    global conn
    table_name_base='AKIAJXNAQH5WHJFPNCXA_' # '201503'
    if mktstring == None:
        mktstring = instance_to_MarketId(instance)
    output=[]
    ondem=[]
    ondemtable = 'on_demand_price'
    #Need to remove avail zone from mkt string argh!
   
    ondem_mktstring = mktstring.replace('a-','-')
    ondem_mktstring = ondem_mktstring.replace('/UNIX','')
    q2 = 'SELECT SpotPrice FROM {} WHERE MarketId=\'{}\' ;'.format(ondemtable, ondem_mktstring)
    d2 = conn.execute(q2)
    ondem = d2.fetchall()

    for month in months :
        table_name = table_name_base+month
        query='SELECT Timestamp, SpotPrice FROM {} WHERE MarketId=\'{}\' ;'.format(table_name, mktstring)
        #print query
        d = conn.execute(query)
        output.extend(d.fetchall())
    return output, ondem[0][0]


def compute_for_all_markets():
    global conn
    init_db_connection()
    #First, get the market list
    q = 'SELECT DISTINCT MarketId FROM AKIAJXNAQH5WHJFPNCXA_201505 ; '
    d = conn.execute(q)
    res = d.fetchall()
    markets = zip(*res)[0]
    #filter markets here! No VPC
    markets = filter(lambda x:x.find('VPC') < 0 , markets)
    for m in markets :
        data = []
        try:
            ts, ondem = read_data_sqlite(None,m)
        except:
            continue
        spot = [(time.mktime(dateutil.parser.parse(t).timetuple()), float(f)) for (t,f) in ts]
        data.append((None, float(ondem), spot))
        
        acdf,acost,amttfs=get_c_a_m(data, plot=False)
        cdf = acdf[0]
        #For avail, the ECDF throws up lots of points with small bids, and not enough for the larger ones.
        #As a result, the random sampling will yield LOWER avail bid ranges.
        #Hence the increase from 100 to 1000, atleast. 
        computed_res = get_bid_bound(zip(cdf.x, cdf.y) , acost[0], amttfs[0])
        save_result(m, computed_res)
       
cnter = 0 
def save_result(mktstring, res_list):
    global cnter
    f = open('all-outputs.txt','a+')
    res_list = [str(x) for x in res_list]
    tow = mktstring+", "+', '.join(res_list)+"\n"
    cnter = cnter+1
    print cnter, tow
    f.write(tow)
    #write to a file also lol
    
    

def c_a_m_graphs():
    global conn
    data = []
    #c3.xlarge seems volatile
    all_instances = [ {'type': 'g2.2xlarge', 'region': 'us-east-1', 'AZ': 'a', 'OS': 'Linux'} ,
                     {'type': 'c3.xlarge', 'region': 'us-east-1', 'AZ': 'a', 'OS': 'Linux'} ,
                     {'type': 'r3.large', 'region': 'us-east-1', 'AZ': 'a', 'OS': 'Linux'} ,
                     {'type': 'm3.medium', 'region': 'us-east-1', 'AZ': 'a', 'OS': 'Linux'} ,
                     {'type': 'd2.8xlarge', 'region': 'us-east-1', 'AZ': 'a', 'OS': 'Linux'}
                     ]
    init_db_connection()
    for i in all_instances :
        ts, ondem = read_data_sqlite(i)
        spot = [(time.mktime(dateutil.parser.parse(t).timetuple()), float(f)) for (t,f) in ts]
        data.append((i, float(ondem), spot))
    #print result[0][0], result[1][0]
    #Set plot=True if graphs are required!
    #m3.medium one is interesting though non-standard. 
    get_c_a_m(data, plot=True, all_costs=None)
    return data

#Cost, Avail, MTTFs, haha
def get_c_a_m(data, plot=False, all_costs=None):
    every_instance, every_cdf, every_cost, every_mttf =[],[],[],[]
    bidrange = np.linspace(0,10,101)[1:]
    
    for mkt in data:
        #price is timestamp (seconds), price
        #Lets normailize everything here? 
        itype, d, prices = mkt
        prices = [(t, float(p)/float(d)) for (t,p) in prices]
        cdf = avail(prices)
        #cdf.x, cdf.y
        cost = expected_cost(bidrange, prices)
        mttfs = get_MTTF(bidrange, prices)
        if itype != None:
            every_instance.append(itype['type'])
        else :
            every_instance.append('')
        every_cdf.append(cdf); every_cost.append(cost); every_mttf.append(mttfs)
     
        #get_bid_bound(itype,sorted(random.sample(zip(cdf.x, cdf.y), 100)) ,cost,mttfs)
    if plot==True:
        #plot_c_a_m(every_instance, every_cdf, every_cost, every_mttf)
        plot_separate(every_instance, every_cdf, every_cost, every_mttf)
        
    if all_costs in range(len(every_instance)):
        pass
        #get_all_costs(every_instance[all_costs], bidrange, every_cdf[all_costs], every_cost[all_costs], every_mttf[all_costs])
        
    return every_cdf, every_cost, every_mttf

######################################################################

def get_all_costs(instance, bidrange, cdf, cost, mttf):
    print instance
    avail_r = zip(cdf.x, cdf.y)
    #print avail_r
    avail_r = resample_cdf(avail_r, bidrange)
    no_ft_cost = no_ft(avail_r, cost, mttf)
    restart_cost = restart(avail_r, cost, mttf)
    ckpt_cost = ckpt(avail_r, cost, mttf)
    migrate_cost = migrate(avail_r, cost, mttf)
    plot_all_costs(bidrange, no_ft_cost, restart_cost, ckpt_cost, migrate_cost)
    return 
    

def plot_all_costs(bidrange, no_ft_cost, restart_cost, ckpt_cost, migrate_cost):
    brc4=['#edf8b1', '#7fcdbb', '#2c7fb8', 'black'] #Sequential
# Yellow teal blue. http://colorbrewer2.org/?type=sequential&scheme=YlGnBu&n=3
    matplotlib.rcParams.update({'font.size': 10})
    matplotlib.rcParams.update({'lines.linewidth': 1.0})
    w=0.10
    g1=0.05
    #Subplots
    fig = plt.figure(tight_layout=True)
    fig.set_size_inches(3.5, 2.5)

    ax = fig.add_subplot(1,1,1)
    X = bidrange
    ax.plot(X, zip(*no_ft_cost)[1], label='None',linestyle='--',color='r')
    ax.plot(X, zip(*restart_cost)[1], label='Restart',linestyle='-', color='r')
    ax.plot(X, zip(*ckpt_cost)[1], label='Checkpointing',linestyle='-', color='black')
    ax.plot(X, zip(*migrate_cost)[1], label='Migration',color='black', linestyle='--')
    
    ax.set_xlim(0,5.0)
    ax.set_ylim(0,1.1)
    ax.set_xlabel('Bid')
    ax.set_ylabel('Expected Cost')
    plt.legend(fontsize='medium')
    plt.savefig("ft-costs.pdf", bbox_inches='tight')
    plt.show()

    #first, resample cdf
######################################################################
def no_ft(avail, cost, mttf):
    #[(b, cost)]
    return cost 
    

#Get revoked with some probability. Then double
def restart(avail, cost, mttf):
    result = []
    
    for i in range(len(cost)):
        b = cost[i][0]
        p = avail[i][1]
        c = cost[i][1]
        ec = c*p + (1-p)*2*c
        result.append((b, ec))

    return result

#Complex tau formula. Recheck!
def ckpt(avail, cost, mttf):
    result = []
    delta = 120.0/3600.0 #in hours!
    
    for i in range(len(mttf)):
        b = mttf[i][0]
        m = mttf[i][1]/3600.0
        tau = math.sqrt(2*delta*m)       
        t = 1.0 + (delta/tau) + (tau/(2*m))
        c = cost[i][1]
        ec = float(c)*t
        print b,m,tau,t,ec
        result.append((b, ec))

    return result

#Similar to restart
def migrate(avail, cost, mttf):
    result = []
    
    for i in range(len(avail)):
        b = avail[i][0]
        p = avail[i][1]
        c = cost[i][1]
        ec = c*p + (1-p)
        result.append((b, ec))

    return result

    
##############################################################################
def find_nearest_idx(array, value):
    idx = (np.abs(array-value)).argmin()
    return idx

#Given a bid, find the closest corresponding availability.  The avail
#array might not be indexed by the same bids because it is generated
#by ECDF function.

def resample_cdf(cdf, bids):
    NPavail = np.array(cdf)
    print NPavail
    newcdf = []
    for b in bids :
        idx = find_nearest_idx(NPavail[:,0], b)
        avail = NPavail[idx, 1]
        newcdf.append((b,avail))
        
    return newcdf

def scale_mttf(mttfs):
    #print mttfs
    bids, mttf = zip(*mttfs)
    f = float(mean(mttf))
    print "mean ", str(f)
    m = map(lambda x:x/f, mttf)
    o = zip(bids,m)
    #print o
    return o
    

def get_bid_bound(cdf, cost, mttf) :
    #random.sample(zip(list_a,list_b), 10)
    output = []
    delta = 0.1
    #We need to resamble the cdf first though. 
    cdf = resample_cdf(cdf, zip(*cost)[0])
    mttf = scale_mttf(mttf)
    for values in cdf, cost, mttf :
    #values = cdf
        brange = 0.0
        l = len(values)
        for start in range(l):
            for end in range(l-1,0,-1) :
                if end > start and abs(values[end][1] - values[start][1]) < delta :
                    brange = max(brange, values[end][0] - values[start][0])
                    
        #put brange somewhere here
        output.append(brange)
    return output
    #write output to file!
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
         mttfat = np.mean(get_failures(prices,b))
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
mcolors=itertools.cycle(['black','red','#7fcdbb','#2b8cbe','0.1'])
mlinestyles = itertools.cycle(['-', '-', '-', '--', '-.']) #, ':'

mmarkers=itertools.cycle(['o', '.', ',', '+','*']) #'s','D','d'
#smooth, dashed, dot-dash, wide
def plot_avail_cdf(ax, instances, cdfs, separate=False):
    lines=[]
    for (i,c) in zip(instances,cdfs):
        X = c.x
        Y = c.y
        lab = i
        l,=ax.plot(X,Y,label=lab,color=mcolors.next(), linestyle=mlinestyles.next())
        lines.append(l)
        
    ax.set_xlabel('Bid price \n (Relative to On-demand price)')
    ax.set_ylabel('Availability CDF')
    ax.set_xlim(-0.1,5.0)
    ax.set_ylim(0.0,1.1)
    #xtnames = [str(x) for x in X]
    #ax.set_xticks(X)
    #xtickNames = ax.set_xticklabels(xtnames)
    if not separate:
        ax.set_title('(a) Availability CDF')
    if separate:
        
        ax.legend(bbox_to_anchor=(1.0,1.2),ncol=3,fontsize='small',fancybox=True)
        plt.savefig('only_avail.pdf',bbox_inches='tight')

        

def plot_cost(ax, instances, costs, separate=False):
    for (i,c) in zip(instances,costs):
        lab = i
        #costs is a [(bid,excost)]
        X,Y = zip(*c)
        ax.plot(X,Y,label=lab,color=mcolors.next(), linestyle=mlinestyles.next())
        
    #ax.set_xlabel('Bid')
    ax.set_xlabel('Bid price \n (Relative to On-demand price)')
    ax.set_ylabel('Cost (Relative to On-demand price)')
    ax.set_xlim(-0.1, 5.0)
    #ax.set_ylim(0.0, 0.5)
    if not separate:
        ax.set_title('(b) Expected Cost')
    if separate:
        ax.legend(bbox_to_anchor=(1.0,1.2),ncol=3,fontsize='small',fancybox=True)
        plt.savefig('only_cost.pdf',bbox_inches='tight')


def plot_mttf(ax, instances, mttfs, separate=False):
    lines = []
    for (i,c) in zip(instances,mttfs):
        lab = i
        #costs is a [(bid,excost)]
        X,Y = zip(*c)
        Y = map(lambda x:x/3600.0 , Y)
        Y = sorted(Y)
        l, = ax.plot(X,Y,label=lab,color=mcolors.next(), linestyle=mlinestyles.next())
        lines.append(l)
        
    ax.set_xlabel('Bid price \n (Relative to On-demand price)')
    ax.set_ylabel('MTBR (hours)')
    ax.set_xlim(-0.1, 5.0)
    ax.set_ylim(0.0, 200)
    if not separate :
        ax.set_title('(c) MTBR')
    if separate:
        ax.legend(bbox_to_anchor=(1.0,1.2),ncol=3,fontsize='small',fancybox=True)
        plt.savefig('only_mttf.pdf',bbox_inches='tight')
   
    return lines

def plot_separate(instances, cdfs, costs, mttfs):
    
    fig = plt.figure(tight_layout=True)
    fig.set_size_inches(5,3.5)
    ax = fig.add_subplot(1,1,1)    
    plot_avail_cdf(ax, instances, cdfs, separate=True)

    fig = plt.figure(tight_layout=True)
    fig.set_size_inches(5,3.5)
    ax = fig.add_subplot(1,1,1)    
    plot_cost(ax, instances, costs, separate=True)

    fig = plt.figure(tight_layout=True)
    fig.set_size_inches(5,3.5)
    ax = fig.add_subplot(1,1,1)    
    plot_mttf(ax, instances, mttfs, separate=True)

    return


def plot_c_a_m(instances, cdfs, costs, mttfs) :
    brc4=['#edf8b1', '#7fcdbb', '#2c7fb8', 'black'] #Sequential
# Yellow teal blue. http://colorbrewer2.org/?type=sequential&scheme=YlGnBu&n=3
    matplotlib.rcParams.update({'font.size': 10})
    matplotlib.rcParams.update({'lines.linewidth': 1.0})
    matplotlib.rcParams.update({'axes.titlesize': 10})
    w=0.10
    g1=0.05
    #Subplots
    fig = plt.figure(tight_layout=True)
    fig.set_size_inches(9,2.5)

    ax = fig.add_subplot(1,3,1)
    plot_avail_cdf(ax, instances, cdfs)
    ax2 = fig.add_subplot(1,3,2)
    plot_cost(ax2, instances, costs)
    ax3 = fig.add_subplot(1,3,3)
    lines = plot_mttf(ax3, instances, mttfs)
    print instances
    #plt.figlegend(lines, instances, 'upper center' )
    fig.legend(lines, instances, 'upper center', ncol=5, bbox_to_anchor=(0.5,1.1),fontsize='medium')
    
    #mttf xlim(0.1, 3)     
    
    plt.savefig('all3.pdf',bbox_inches='tight')
    plt.show()
        
       
def instance_to_MarketId(i) :
    osname = {'Linux':'Linux/UNIX'}
    return i['region']+i['AZ']+'-'+osname[i['OS']]+'-'+i['type']
    
    
    
#############################################################################

def read_data_file():
    df_c1medium = pandas.read_csv("us-east-1a_c1.medium_Linux", header=None, names=["Time", "Price"], parse_dates=True)

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


def instance_from_filename(f) :
    #ap-northeast-1b_m1.medium_Linux
    instance_dict={'type': 'm1.small',
                   'region': 'us-east-1',
                   'AZ': 'a',
                   'OS': 'Linux',
                   }
    
    fs = f.split("_")
    try:
        instance_dict['OS']=fs[-1]
        instance_dict['type']=fs[-2]
        r=fs[0]
        instance_dict['region']=r[:-1]
        instance_dict['AZ']=r[-1:]
    
        print instance_dict
        return instance_dict
    except Exception:
        print "cant parse " + str(Exception)
        return None



######################################################################    
if __name__ == "__main__" :
    c_a_m_graphs()
    #compute_for_all_markets()
