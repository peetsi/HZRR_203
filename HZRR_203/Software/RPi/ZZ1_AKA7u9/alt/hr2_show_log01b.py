#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
Created on 2020.10.05 

@author: pl
"""




import glob
import time
import numpy as np
import matplotlib.pyplot as plt
import time
import sys
from operator import itemgetter


# import select_log as sellog
import rr_parse as parse

def select_log_file():
    flist = glob.glob("log/*.dat")
    flist.sort()
    fileNr=0
    for file in flist:
        fileNr += 1
        print("%d  -  %s"%(fileNr, file))
    #fileIndex = int(input("Wahl ")) - 1
    fileIndex = 0


    if len(flist) == 0:
        print( "Keine Log-Dateien gefunden" )
        return []
    
    # extract date and time from selected file plpl
    # "logHZ-RR_20161228_043534.dat"  (typical filename)
    fileName = flist[fileIndex]
    return [fileName]






if __name__ == "__main__" :
    args = sys.argv
    nargs = len(args)
    print(args)

flist  = select_log_file()
for file in flist:
        print("Lese ein: %s"%(file))
        logf = open(file,'r')
        lineCnt=0
        allDat=[]
        for line in logf :
            lineCnt += 1
            l0=line.strip()
            # parse return value is:
            #   (zDateSec,hkr,module,command,control,protVer,modTStamp,summer,
            #    vlm,rlm,vle,rle,rls,ven,err,fix,tmo,tan)
            # or in case of error:
            #   (1,errNr)
            p = list( parse.rr_parse(l0) )
            #print(lineCnt, p)
            l = len(p)
            if l > 2:
                #print(l,p)
                allDat.append(p)


allDat.sort(key=itemgetter(2,4,0))

#for p in allDat:
#    if p[2]==1 and p[4]==1:
#        print(p)

# "20201002_092636 0401 HK2 :0002041b t85.0 0 VM-127.0 RM 41.7 VE 70.0 RE 40.0 RS  0.0 P107 E0000 FX41 M43 A1"
# [1601899779.0, 2, 1, 2, 1, 'b', 265783.1, 0, -127.0, 38.2, 70.0, 38.4, 44.0, 86.0, 2, 20.0, 669.0, 27.0]

#for mod in [30]: #
modules = [1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,30]
nm = len(modules)
for mod in modules:
    for reg in [1,3]:
        ri = reg-1

        teil = []
        for x in allDat:
            if x[2]==mod and x[4]==reg:
                teil.append(x)
        if teil==[]:
            continue
        
        rll=[]
        vll=[]
        pll=[]
        for l0 in teil:
            rl=l0[9]
            rll.append(rl)
            vl=l0[10]
            vll.append(vl)
            pl=l0[13]
            pll.append(pl/10.0)

        al = len(rll)
        t = range(al)
        #t0 = t[0:al]
        plt.plot(t,rll,"-",label="mod%dRLr%d"%(mod,reg))
        plt.plot(t,vll,":",label="mod%dVLr%d"%(mod,reg))
        #plt.plot(t,pll,"-",label="mod%dP%%%d"%(mod,reg))

    picName = "Bilder/%s.png"%(file)
    plt.title(picName)

    plt.grid("both")
    plt.xlabel("t")
    plt.ylabel("degC/%")
    plt.legend()
    plt.savefig(picName) 
    plt.show()



