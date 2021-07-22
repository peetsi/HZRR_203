#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
Created on 2020.11.16
Version 4a 

show draft values from Annette-Kollwitz-Anger installation of HZRR-200

@author: pl
"""

import os
import glob 
from operator import itemgetter
import numpy as np
import time
import matplotlib.pyplot as plt

import rr_parse as parse


def get_hostname():
    f=open("/etc/hostname","r")
    name = f.read()
    name = name.strip()
    return name


def select_log_files(path):
    """ in directory 'pathLogFiles' copy all log*.dat files into one file; return this filename. """
    path=path.rstrip("/")
    flist = glob.glob(path+"/log*.dat")
    flist.sort()
    fcnt=0
    for file in flist:
        fcnt += 1
        print(fcnt, os.path.basename(file))
    print("Verbinde alle Log-Dateien im Verzeichnis '%s'"%(path))
    if len(flist) == 0 :
        print( "Keine Log-Dateien gefunden / abgebrochen" )
        return None

    # *** concatenate all files of form:
    #     "<path>/logHZ-RR_20201019_000958.dat"
    vonFile = os.path.basename(flist[0]).rsplit(".dat")
    bisFile = os.path.basename(flist[-1]).rsplit(".dat")
    print("Verbinde dateien von '%s' bis '%s'"%(vonFile[0],bisFile[0]))

    # make new filename
    sVon = vonFile[0].lstrip("logHRZ-RR_")
    sBis = bisFile[0].lstrip("logHRZ-RR_")
    sumFileName = "/sumHZ-RR_" + sVon + "-" + sBis + ".dat"
    print("speichere das Ergebnis in file: ",sumFileName)
    
    # write to output file
    fout=open(path + sumFileName,"w+")
    rzeile=0
    wzeile=0
    print("add file Nr. ",end="")
    for file in flist:
        i = flist.index(file) + 1
        print(i,end=" ")
        fin=open(file,"r")
        for line in fin:
            rzeile+=1
            if len(line) >100:   # ignore short lines - they are incomplete
                wzeile+=1
                fout.write(line)
        fin.close()
    fout.close()
    print()
    print("%d Zeilen gelesen, %d Zeilen geschrieben"%(rzeile,wzeile))
    return (sumFileName)


def read_all_data( logfileSum ):
    """ read data from logfile lines into a big list; return this list """
    try:
        fin = open(logfileSum,"r")
    except Exception as e:
        print(e)
        print("no file to plot")
        return None
    adat=[]
    lineCnt=0
    datCnt =0
    adat = []
    for line in fin:
        lineCnt += 1
        l0 = line.strip()
        # typ. l0:
        # [1604985134.0, 2, 1, 2, 2, 'b', 49778.1, 1, 70.0, 40.0, 70.0, 40.0, 0.0, 0.0, 4, 20.0, 0.0, 0.0]
        p = list( parse.rr_parse(l0) )
        #print(lineCnt, p)
        l = len(p)
        if l > 14:
            #print(l,p)
            # index =        0   1   2  3   4    5        6   7       8     9     10    11      12    13  14    15   16   17
            # 18 [1604963488.0,  2,  1, 2,  1, 'b', 28134.8,  1, -127.0, 32.3, -79.0, 38.4,   32.0,  0.0,  2, 21.0, 0.0, 0.0]
            # name=    secEpoc cmd mod HK Reg prot  nanoTic S/W  VLMess   RLM  VLeff  RLeff RLsoll  VPos ERR   Fix    M    A
            # VPos: 0-999, Fix: fixed position reached, M: motor on-time, A: motor Limits reached (Anschlag)
            datCnt += 1
            
        # debug: comment out for normal operation
        #if lineCnt > 1000:
        #    pass               # stop for debugging only
        #    break   # for debug only
        
        #print("%d lines read - %d used"%(lineCnt,datCnt))
        adat.append(p)
    adat.sort(key=itemgetter(2,4,0))   # sortiere columns 2 (ModulNr), 4(subAdr) und 0(time)
    return adat    
        

def plot_all(picPath,adat):
    """ plot all hr2data in one diagram. """
    cm2i = 1.0/2.54  # factor cm to insh
    modules = list( set( [x[2] for x in adat] ) ) # extract all module numbers
    nmod = len(modules)
    #fig = plt.figure(figsize=(40*cm2i,nmod*8*cm2i))
    fig,axs = plt.subplots(nmod,2,figsize=(40*cm2i,nmod*8*cm2i))
    print("plot data; mod Nr.= ",end="")
    for mod in modules:
        modIdx = modules.index(mod)
        #print("mod=%d --- modIdx=%d"%(mod,modIdx))
        for regNr in [1,3]:
            ri = regNr-1
            # extract all data from mod/regNr
            teil=[]
            for dat in adat:
                if dat[2]==mod and dat[4]==regNr:
                    dat[5] = ord(dat[5])       # rplace protocol version 'b' by a number
                    teil.append(dat)
            #print("teil: mod=%d reg=%d"%(mod,regNr),len(teil), teil)

            # plot data from teil:
            teilA = np.array(teil)
            if teilA.size > 0:
                # *** calculate times and time-axis (x-axis)
                t0        = teilA[0,0]
                ts        = time.localtime( t0 )
                t1        = teilA[ -1,0]
                te        = time.localtime( t1 )
                tSecStart = ts[3]*3600 + ts[4]*60 + ts[5]  # seconds from midnight
                t         = teilA[:,0] - t0 + tSecStart    # seconds from midnight
                th        = t / 3600.0                     # times in hours
                
                # *** prepare plot position
                diagPos = 2*modIdx+ri+1
                #print("diagPos=",diagPos)
                # ax = plt.subplot(nmod+1,2,diagPos)
                
                # *** set headline and filename
                if mod==1 and regNr==1:
                    datimStart = time.strftime('%Y-%m-%d %H%M%S',ts)
                    datimEnd   = time.strftime('%Y-%m-%d %H%M%S',te)
                    hostName   = get_hostname()
                    plt.title("HR2-"+hostName+"-"+datimStart+"-"+datimEnd)
                    filename = "hr2_diagram_"+datimStart+"-"+datimEnd+".png"


                # *** extract plot-data (y-axes)
                # index =        0   1   2  3   4    5        6   7       8     9     10    11      12    13  14    15   16   17
                # 18 [1604963488.0,  2,  1, 2,  1, 'b', 28134.8,  1, -127.0, 32.3, -79.0, 38.4,   32.0,  0.0,  2, 21.0, 0.0, 0.0]
                # name=    secEpoc cmd mod HK Reg prot  nanoTic S/W  VLMess   RLM  VLeff  RLeff RLsoll  VPos ERR   Fix    M    A
                vlMess    = teilA[:,8]
                rlMess    = teilA[:,9]
                vlEff     = teilA[:,10]
                rlEff     = teilA[:,11]
                rlSoll    = teilA[:,12]
                vPos      = teilA[:,13] / 10.0
                # *** fit values in diagram
                vlMessP   = [max(x,0.0) for x in vlMess]    # remove negative values
                rlMessP   = [max(x,0.0) for x in rlMess]    # remove negative values
                vlEffP    = [max(x,0.0) for x in vlEff]     # remove negative values
                rlEffP    = [max(x,0.0) for x in rlEff]     # remove negative values
                rlSollP   = [max(x,0.0) for x in rlSoll]    # remove negative values
                venPos    = vPos
                # *** plot ALL values
                if regNr==1 : xpos=0 
                else: xpos=1
                #axs[modIdx,xpos].plot(th,vlMessP,"o",linestyle="--", label="%d/%dvlM"%(mod,regNr))
                axs[modIdx,xpos].plot(th,vlMessP,linestyle="--", label="%d/%dvlM"%(mod,regNr))
                axs[modIdx,xpos].plot(th,rlMessP,linestyle="-", label="%d/%drlM"%(mod,regNr))
                if mod != 30:
                    axs[modIdx,xpos].plot(th,vlEffP, linestyle="--", label="%d/%dvlReg"%(mod,regNr))
                    axs[modIdx,xpos].plot(th,rlEffP, linestyle="-", label="%d/%drlReg"%(mod,regNr))
                    axs[modIdx,xpos].plot(th,rlSollP,linestyle="-.", label="%d/%drlSoll"%(mod,regNr))
                    axs[modIdx,xpos].plot(th,venPos, linestyle=":", label="%d/%dvPosRel"%(mod,regNr))
                
                # *** replace time-tics with hours of the day
                xlocs = axs[modIdx,xpos].get_xticks()
                xlabels = axs[modIdx,xpos].get_xticks()
                #print("xlocs=",xlocs,"; xlabels=",xlabels)
                xticlabels = [str(t%24) for t in xlocs]
                #plpl axs[modIdx,xpos].set_xticklabels(xticlabels)
                
                # *** vertical lines at 00:00
                hourMin = min(xlabels)
                hourMax = max(xlabels)
                vLinePos=[]
                for h in np.arange(hourMin,hourMax):
                    if h%24 == 0:
                        vLinePos.append(h)
                        axs[modIdx,xpos].vlines(h,0,100)
                
                axs[modIdx,xpos].grid("both")
                axs[modIdx,xpos].set_ylabel("degC/%")
                axs[modIdx,xpos].legend(fontsize="x-small")
                axs[modIdx,xpos].set_xlabel("t / h")

                
    plt.tight_layout()
    picName = picPath + filename
    plt.savefig(picName)
    #plt.show()
    plt.close()

 

if __name__ == "__main__" :
    logfilePath = "log/plotlog/"
    picturePath = logfilePath + "Bilder/"
    sumFile = select_log_files( logfilePath )
    if sumFile==None:
        exit(1)
    # read measured values into a big data array
    adat = read_all_data(logfilePath+sumFile)
    plot_all(picturePath,adat)
    
    
    
    





