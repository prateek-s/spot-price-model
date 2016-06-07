#!/bin/bash
# Failure inter-arrival times distribution
import os,sys,datetime,time,dateutil.parser
import statsmodels.discrete
import scipy.stats
import numpy as np
import matplotlib.pyplot as plt

################################################################################

ONDPrices = {'m2.2xlarge':0.5,
             }

def inter_arrival_times(instance, trace_file):
    BID=0.5 #On-demand price
    timebuf = 3600 #1 hour
    first_failure = 0 #Time of first failure. Maybe ignore it?    
    f = open(trace_file, 'r')
    lines = f.readlines()
    pricetrace = parse_lines(lines) #(time, price tuples)
    failures = get_failures(pricetrace, BID, timebuf)    
    faildist = to_dist(failures)
    plot_stuff(failures, faildist, BID, timebuf, instance)
    
################################################################################

def to_dist(failures):
    if len(failures) == 0 :
        return []
    dis=scipy.stats.expon.fit(failures)
    do_tests(failures, dis)
    #Cumulative thingy from http://stats.stackexchange.com/questions/70229/testing-for-poisson-process
    
    
    return dis

def do_tests(failures, dis):
    size = max(failures)
    mle = sum(failures)/float(len(failures))
    print "MLE lambda= "+str(mle)
    print "Scipy mu, sigma= "+str(dis)
    ks = scipy.stats.kstest(failures,'expon')
    print "Kolmogorov smirnov= "+str(ks)
    anderson = scipy.stats.anderson(failures,'expon')
    print "Anderson= "+str(anderson)
    x=scipy.arange(size)
    dist = scipy.stats.expon
    param = dis
    pdf_fitted = dist.pdf(x, *param[:-2], loc=param[-2], scale=param[-1]) * size
#    chisquared = scipy.stats.chisquare(failures)
    print failures
    print ">>>>>>>>>>>>>>>>>>>>>>>"
    print pdf_fitted
    print "Chisquared "+str(chisquared)
    
################################################################################
    
def plot_stuff(f, dis, bid, timebuf, instance):
    num_bins = 40 #who really knows?
    size=max(f)
    #f = np.cumsum(f)
    h = plt.hist(f, num_bins,color='0.95')
    dist_names = ['expon', 'pareto', 'rayleigh', 'norm']
    x = scipy.arange(size)
    for dist_name in dist_names:
        dist = getattr(scipy.stats, dist_name)
        param = dist.fit(f)
        print "Param for "+dist_name+": "+str(param)
        #Right place to pickle f, filename, dist_name, param
        pdf_fitted = dist.pdf(x, *param[:-2], loc=param[-2], scale=param[-1]) * size
        plt.plot(pdf_fitted, label=dist_name,linewidth=1.5)

    plt.legend(loc='upper right')
    plt.xlabel('Inter arrival time (s)')
    plt.ylabel('Freq')
    graphtitle = instance['type']+instance['region']+instance['AZ']+"@"+str(bid)
    plt.title(graphtitle)
    print "Plot:"
    basedir="/home/prateeks/NSDI2015-SparkSpot/graphs/iat"
    plt.savefig(os.path.join(basedir,graphtitle+".pdf"))
    #plt.show()


################################################################################
    
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

################################################################################

def get_failures(pricetrace, bid, timebuf):
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

    print "Number of failures: "+str(len(out))
    return out       

################################################################################

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


################################################################################

def all_iat(argv):
    d=argv[1]
    if not os.path.isdir(d) :
        f = os.path.split(d)[-1]
        instance = instance_from_filename(f)
        if instance is not None:
            inter_arrival_times(instance, d)
        return
    
    for f in os.listdir(d):
        fp = os.path.join(d,f)
        instance = instance_from_filename(f)
        if instance is not None:
            inter_arrival_times(instance, fp)

################################################################################


all_iat(sys.argv)

#inter_arrival_times(sys.argv[1])
