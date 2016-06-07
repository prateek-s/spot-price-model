# -*- coding: utf-8 -*-
"""
Created on Wed Mar  2 13:15:56 2016

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
import scipy.stats
def my_to_float(x):
    #print type(x)
    #if not np.isfinite(x):
    #    print x
    y = str(x)
    z = y.replace('inf','10')
    return float(z)

def my_to_date(x):
    dt = dateutil.parser.parse(x)
    return str(dt.year)

def read_all_data():
    fname = 'm1l.txt'
    df = pd.read_csv(fname)
    #avail cost mttf
    df.columns = ['date','cost']
    #Clean the data now 
    df['cost'] = df['cost'].apply(my_to_float)
    df['date'] = df['date'].apply(my_to_date)
    #print df['avail']
    print df
    return df

def plot_cost_boxplot(df):
    brc4=['#edf8b1', '#7fcdbb', '#2c7fb8', 'black'] #Sequential
# Yellow teal blue. http://colorbrewer2.org/?type=sequential&scheme=YlGnBu&n=3
    matplotlib.rcParams.update({'font.size': 10})
    matplotlib.rcParams.update({'lines.linewidth': 1.0})
    w=0.10
    g1=0.05
    #Subplots
    fig = plt.figure(tight_layout=True)
    fig.set_size_inches(3.5,2.5)

    ax = fig.add_subplot(1,1,1)
    
    #cdf = ECDF(df['avail'])
    #X=cdf.x
    #Y=cdf.y
    #ax.plot(X,Y)
    data = []
    years = ['2010','2011','2012','2013','2014','2015']
    kur=[]
    skews=[]
    for y in years:
        cost = df[df['date'] == y]['cost']
        k = scipy.stats.kurtosis(cost)
        skews.append(scipy.stats.skew(cost))
        kur.append(k)
        data.append( cost )
        
   
    plt.boxplot(data , whis=[1,95], notch=True, showfliers=True, sym='',labels=years)
    #showmeans=True, showfliers=False
    j = 0 
    yvals = [0.3, 0.5, 0.8, 1.3, 0.5, 0.3]
    for (j,s) in enumerate(skews):
        #print j, k
        plt.annotate('{:.2f}'.format(s), xy=(j+0.7, yvals[j]),rotation=0)
       
    
    plt.ylabel('Spot price distribution')
    ax.set_ylim(-0.1,1.5)

    plt.savefig('allyears.pdf',bbox_inches='tight')    
    plt.show()

def plot_avail_boxplot(df):
    brc4=['#edf8b1', '#7fcdbb', '#2c7fb8', 'black'] #Sequential
# Yellow teal blue. http://colorbrewer2.org/?type=sequential&scheme=YlGnBu&n=3
    matplotlib.rcParams.update({'font.size': 10})
    matplotlib.rcParams.update({'lines.linewidth': 1.0})
    w=0.10
    g1=0.05
    #Subplots
    fig = plt.figure(tight_layout=True)
    fig.set_size_inches(5,3) #3.5,2.5 

    ax = fig.add_subplot(1,1,1)
    
    #cdf = ECDF(df['avail'])
    #X=cdf.x
    #Y=cdf.y
    #ax.plot(X,Y)
    data = []
    years = ['2010','2011','2012','2013','2014','2015']
    for y in years:
        cost = df[df['date'] == y]['cost']
        avail = ECDF(cost)
        ax.plot(avail.x, avail.y, label=y)
            
    #ax.ylabel('Availability')
    #ax.xlabel('Bid')
    #ax.set_ylim(-0.2,6)

    plt.savefig('allyears-cdf.pdf',bbox_inches='tight')    
    plt.show()


def main():
    df = read_all_data()
    plot_cost_boxplot(df)
    #plot_avail_boxplot(df)    

if __name__ == '__main__' :
    main()
