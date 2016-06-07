# -*- coding: utf-8 -*-
"""
Created on Wed Mar  2 09:30:46 2016

@author: prateeks
"""

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

def my_to_float(x):
    #print type(x)
    #if not np.isfinite(x):
    #    print x
    y = str(x)
    z = y.replace('inf','10')
    return float(z)

def cmy_to_float(x):
    #print type(x)
    #if not np.isfinite(x):
    #    print x
    y = str(x)
    z = y.replace('inf','10')
    return float(z)


def read_all_data():
    fname = 'all-outputs.txt'
    df = pd.read_csv(fname)
    #avail cost mttf
    df.columns = ['instance','avail','cost','mttf']
    #Clean the data now 
    df['avail'] = df['avail'].apply(my_to_float)
    df['cost'] = df['cost'].apply(cmy_to_float)
    df['mttf'] = df['mttf'].apply(my_to_float)
    #print df['avail']
    print df
    return df


def plot_all_cdfs(df):
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
    
    plt.boxplot([df['avail'], df['cost'], df['mttf']], 1, 'g', labels=["Avail.","Cost","MTBR"])
 
    plt.ylabel('Bid range length')
 
    plt.savefig('boxplot.pdf',bbox_inches='tight')

    plt.show()


def main():
    df = read_all_data()
    plot_all_cdfs(df)    

if __name__ == '__main__' :
    main()
