#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jan 16 21:22:10 2017

@author: pl

select log files and read all values of suitable files
in one big data array for faster processing


"""


import glob
import numpy as np
import time
import os
import heizkreis_config as hkr_cfg
import rr_parse as parse

# dictionary defining an index from variable names
val  = {"vIdx":0,
        "vSoW":1,           # d;     summer=1; winter=0
        "vMod":2,           # d;     module number
        "vVlm":3,           # degC;  Vorlauf, measured
        "vRlm":4,           # degC;  Ruecklauf, measured
        "vVle":5,           # degC;  Vorlauf, evaluation base
        "vRle":6,           # degC;  Ruecklauf, evaluation base
        "vSol":7,           # degC;  Solltemperatur, set-temperature
        "vVen":8,           # %;     estimated valve position 0..100%
       }

#global av
global heizkreis
global modules
global modTVor     # Modul Nr. mit zentraler Vor- unf Ruecklauftemperatur
global modSendTvor
global filtFakt


h = hkr_cfg.get_heizkreis_config()
(heizkreis, modules, modTVor, modSendTvor, dtLog, filtFakt) = h


def select_first_file_index( flist, lastFileIndex, firstSec ):
    err = 0
    idx = lastFileIndex-1
    while idx >= 0 :
        hs = flist[idx].split("_")
        try:
            datum=hs[1]
            zeit =hs[2].split(".")[0]
        except Exception as e:
            print(e)
            err = 3
        else:
            hstr = datum+"_"+zeit

        try:
            sec = time.mktime( time.strptime(hstr,"%Y%m%d_%H%M%S") )
        except Exception as e:
            print(e)
            err = 4

        if sec < firstSec:
            break
        idx -= 1

    if err!=0:
        return -1
    elif idx >= 0 :
        #print( sec, firstSec )
        return idx
    else:
        return 0








def select_logfiles( choice ):
    # list all log-files in "./log/*"
    # choice    "N" <=> ask; 'E' <=> Ende; 'L' <=> Letzter Tag; 'Z' <=> letzte 2 Tage
    err = 0
    flist = glob.glob("log/log*.dat")
    flist.sort()

    print("flist=",flist)
    
    fileNr = 0;
    for file in flist:
        fileNr += 1
        if (choice=="N" or choice=="n") :
            print("%d  -  %s"%(fileNr, file))
    fileIndex = fileNr-1

    if len(flist) == 0:
        print( "Keine Log-Dateien gefunden" )
        return []
    
    # extract date and time from selected file plpl
    # "logHZ-RR_20161228_043534.dat"  (typical filename)
    fileIndex = int(input("Wahl:"))-1
    fileName = flist[fileIndex]
    
    print("selected file nr=%d, name=%s"%(fileIndex+1,fileName))
    hs = fileName.split("_")
    try:
        datum=hs[1]
        zeit =hs[2].split(".")[0]
        print(datum,zeit)
    except Exception as e:
        print(e)
        err = 1
    else:
        hstr = datum+"_"+zeit
        try:
            lastSec = time.mktime( time.strptime(hstr,"%Y%m%d_%H%M%S") )
        except Exception as e:
            print(e)
            err = 2

    print("err=",err)
    if err == 0 :
        #print("lastSec=%d"%(lastSec))
        ende = False
        while not ende:
            if choice == "N":
                print("E)nde; L)etzter Tag; Z)wei letzte Tage; 1,2,3... von Datei")
                print("Wahl:", end="")
                w=input()
            else:
                w=choice

            if w=="E" or w=="e":
                return[]

            if w=="L" or w=="l":
                firstSec = lastSec - 3600 * 24
                firstFileIndex = select_first_file_index( flist, fileIndex, firstSec )
                ende = True

            elif w=="Z" or w=="z":
                firstSec = lastSec - 3600 * 48
                firstFileIndex = select_first_file_index( flist, fileIndex, firstSec )
                ende = True

            else:
                try:
                    w0=int(w)-1
                except Exception as e:
                    print(e)
                else:
                    if 0 < w0 <= lastFileIndex+1 :
                        firstFileIndex = w0
                        if w0 != lastFileIndex:
                            w=input("Bis Datei Nr:")
                            try:
                                w0=int(w)-1
                            except Exception as e:
                                print(e)
                            else:
                              if firstFileIndex <= w0 <= lastFileIndex:
                                  lastFileIndex=w0
                        ende = True

        fl = []

        for i in range(firstFileIndex,lastFileIndex+1):
            fl.append(flist[i])
        return fl






# ----------------
# ----- main -----
# ----------------



# test:
#
#flist = select_logfiles("N")
if __name__ == "__main__" :
    flist = select_logfiles("N")
    print( flist )

