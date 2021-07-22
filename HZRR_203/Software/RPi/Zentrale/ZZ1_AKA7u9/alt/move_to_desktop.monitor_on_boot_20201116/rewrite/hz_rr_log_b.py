#!/usr/bin/env python3

import sys
import time
import os
import glob
import numpy as np

import heizkreis_config as hkr_cfg
import rr_parse as parse
import usb_ser_b as us
import modbus_b as mb
import hz_rr_log as lg

import hz_rr_config as cg
global cg
cg = cg.conf(cg.configfile_n)

global outFileName, modules, modAdr, cn2, cn4
txCmd=""
rxCmd=""
outFileName=""

log_on_usb = cg.r('system','logOnUSB')
#windows: locPath="D:\\coding\\move_to_desktop.monitor_on_boot\\log\\"

locPath=cg.r('system','logPath_local')
if log_on_usb:
    locPath=cg.r('system','logPath_USB')
print("logging to:", locPath)
fn=time.strftime(locPath+cg.r('system','logFileNameMask'))

modAdr=4
subAdr=1

lg.outFileName=outFileName
lg.locPath = locPath
lg.modAdr  = modAdr
lg.subAdr  = subAdr

print("new file:",fn)
try:   
    odat = open(fn,'w')
except Exception as e:
    print("error opening file:", fn, "\r","err:",e)
odat.close()

#us.read_stat(modadr,subadr)


def rr_log():
    global vlZen                # Vorlauftemperatur von Zentrale
    global heizkreis,modules,modTVor,modSendTvor,dtLog,filtFakt
    global ser, outFileName, modAdr

    us.read_stat(modAdr,subAdr)
    time.sleep(1.0)

    dtNewFile = 60.0*60.0*6.0    # sec; to make a new file
    dtLog     = 60.0* 3.0        # sec; log interval; default value
    
    us.ser_reset_buffer()
    timeNewFile = time.time() + dtNewFile
    ende = False

    while not ende:
        lg.check_log_file()
        h = hkr_cfg.get_heizkreis_config(0)
        if len(h) > 5:
        #    (heizkreis, modules, modTVor, modSendTvor, dtLog, filtFakt) = h
            (lg.heizkreis, lg.modules, lg.modTVor, lg.modSendTvor, lg.dtLog, lg.filtFakt) = h
        else:
        #   # some default values
        #   heizkreis   = 0
        #   modules     = []
        #   modTVor     = 0
        #   modSendTvor = []
        #   dtLog       = 180    # time interval to log a data set
        #   filtFakt    = 0.1
            lg.heizkreis = 0
            lg.modules = 0
            lg.modTVor = 0
            lg.modSendTvor = []
            lg.dtLog = 180
            lg.filtFakt = 0.1

        nextTime = time.time() + dtLog
        lg.write_all_stat()
        # (1) geaendert 20180514:
        # alt:
        # if modTVor > 0 and vlZen >= 40.0 :
        #   do not send if no T.vl measured or VL Temp. is too low
        # neu:
        
        while (time.time() < nextTime):
            time.sleep( 1.0 )

        print(".",end="")
        if time.time() > timeNewFile :
            timeNewFile = time.time() + dtNewFile
            print("close log-file and start a new one")
            odat.close()
            lg.outFileName=""

    us.ser.close()




if __name__ == "__main__" :
    print("*****************************")
    print("hz-rr-log")
    print("creating logfile")
    print("*****************************")

    us.ser_check()

    while(True):
        rr_log()
    
    us.ser.close()


