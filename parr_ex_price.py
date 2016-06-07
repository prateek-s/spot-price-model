import os
import sys
import urllib2
import urllib
import re
import itertools 
import multiprocessing


def fetch_spot_prices(pool) :

    Region=["US East (N. Virginia)" ,
            "US West (Oregon)" ,
            "US West (Northern California)" ,
            "EU (Ireland)" ,
            "Asia Pacific (Singapore)" ,
            "Asia Pacific (Tokyo)" ,
            "South America (Sao Paulo)" ,
            "Asia Pacific (Sydney)"] 
    
    Zone=[  "us-east-1a" , 
            "us-east-1b" , 
            "us-east-1c" , 
            "us-east-1d" ,
            "us-west-1a" ,
            "us-west-1b" ,
            "us-west-1c" ,
            "us-west-2a" ,
            "us-west-2b" ,
            "us-west-2c" ,
            "eu-west-1a" ,
            "eu-west-1b" ,
            "eu-west-1c" ,
            
            "ap-southeast-1a" ,
            "ap-southeast-1b" ,
            
            "ap-northeast-1a" ,
            "ap-northeast-1b" ,
            "ap-northeast-1c" ,
            
            "sp-east-1a",
            "sp-east-1b",
            
            "ap-southeast-2a" ,
            "ap-southeast-2b" ,
            
            ]
    
    
    Type=[  "m1.small" , 
            "m1.medium" , 
            "m1.large" , 
            "m1.xlarge" , 
            "t1.micro" , 
            "m2.xlarge" , 
            "m2.2xlarge" , 
            "m2.4xlarge" , 
            "c1.medium" , 
            "c1.xlarge" , 
            "cc1.4xlarge" , 
            "cc2.8xlarge" , 
            "cg1.4xlarge" , 
            "m3.xlarge" , 
            "m3.2xlarge"  ]
    
    
    Product=[  "Linux/UNIX" , 
               "SUSE Linux" , 
               "Windows" , 
               "Linux/UNIX (Amazon VPC)" , 
               "SUSE Linux (Amazon VPC)" , 
               "Windows (Amazon VPC)" 

               ]

    simple_pname={  "Linux/UNIX":"Linux" , 
               "SUSE Linux":"SUSE" , 
               "Windows" : "Windows" , 
               "Linux/UNIX (Amazon VPC)" : "LinuxVPC", 
               "SUSE Linux (Amazon VPC)" : "SUSEVPC" , 
               "Windows (Amazon VPC)" : "WindowsVPC" 
               }

    
    pname=["Linux",
           "SUSE",
           "Windows",
           "Linux_VPC",
           "SUSE_VPC",
           "Windows_VPC"]
    
    excurl = "curl 'http://spot.scem.uws.edu.au/ec2si/Download.jsp?Zone=us-east-1a&Type=m1.large&Product=Linux/UNIX&IntervalFrom=2009-01-01%2000:00:00.0&IntervalTo=2014-12-31%2000:00:00.0'"

    #    for (z,t,p) in itertools.product(Zone,Type,Product) :
    #    fetch_the_data(z,t,p)
    pool.map(fetch_the_data, list(itertools.product(Zone,Type,Product)))
    return 0

def test_one():
    fetch_the_data(('us-east-1a','m1.large','Linux/UNIX'))

def fetch_the_data(i):
    z=i[0]
    t=i[1]
    p=i[2]
    simple_pname={  "Linux/UNIX":"Linux" , 
               "SUSE Linux":"SUSE" , 
               "Windows" : "Windows" , 
               "Linux/UNIX (Amazon VPC)" : "LinuxVPC", 
               "SUSE Linux (Amazon VPC)" : "SUSEVPC" , 
               "Windows (Amazon VPC)" : "WindowsVPC" 
               }

    spot_url = 'http://spot.scem.uws.edu.au/ec2si/Download.jsp'
    values = {'Zone' : z ,
              'Type' : t ,
              'Product' : p ,
              'IntervalFrom' : '2009-01-01 00:00:00.0' ,
              'IntervalTo' : '2016-05-31 00:00:00.0'
              }
    data = urllib.urlencode(values)
    req = urllib2.Request(spot_url, data)
    print values 
    response = urllib2.urlopen(req)
    the_page = response.read()
    filename = z+"_"+t+"_"+simple_pname[p]
    fhandle = open(filename,"a")
    fhandle.write(the_page)
    fhandle.close()        
    print "All Done!"
    return 0


if __name__ == "__main__" :
    #pool = multiprocessing.Pool(processes=40)              # start 4 worker processes
    #fetch_spot_prices(pool)
    
    test_one()