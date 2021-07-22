#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
HZ-RR012 log function

Created on 06.12.2016
@author: Peter Loster (pl)

history:
hz_rr_log.py         06.12.2016  pl  initial release
hz_rr_log_Winter.py  14.05.2018  pl  (1) Simulation hoehere VL Temp
                                     fuer ganzjaehrigen Winterbetrieb
                                     send_all_Tvor() geaendert
                     Nur vorlaeufig - Ergebnis beobachten

"""
import sys
import time
import os
import glob
import numpy as np
import usb_ser as us
import modbus  as mb
import heizkreis_config as hkr_cfg
import rr_parse as parse

# ----------------
global modules
global odat
global vlZen
global vle1
global filtFakt
global p
global heizkreis, modTVor


global modules
global odat
global vlZen
global vle1
global filtFakt
global p
global heizkreis, modTVor
global filtFakt

# some initial values
filtFakt = 0.1    # Filter 2. Ordnung; filtFakt = Bewertung des neuen Wertes
vlZen = 0.0       # temperature from Zentrale Vorlauf; 0 -> no temperature
vle1  = 0.0       # initial value


print("*****************************")
print("hz-rr-log")
print("creating logfile")
print("*****************************")

def wait(s) :
    pass
    #print(s)
    #time.sleep(2.0)

wait('start')

#locPath="/home/pi/Desktop/monitor/"
locPath="./"
txCmd=""
rxCmd=""
outFileName=""
fn=time.strftime(locPath+'log/newLogStart_%Y-%m-%d_%H:%M:%S.dat')
print("new file:",fn)

odat = open(fn,'w')
odat.close()

def check_log_file():
    global odat, outFileName
    if outFileName == "" \
    or odat.closed :
        # open new file
        outFileName=locPath+'log/logHZ-RR_'+time.strftime('%Y%m%d_%H%M%S.dat')
        odat = open( outFileName, 'w' )


def read_stat( modAdr, contr ) :
    # modAdr e {1..30}
    # contr  e {1..4}
    us.ser_reset_buffer()
    global txCmd, rxCmd
    txCmd = mb.wrap_modbus( modAdr, 2, contr, "" )
    #print('sende:  %s'%(txCmd))
    rxCmd = us.txrx_command( txCmd )
    #print('empfange: %s'%( rxCmd ) )


def write_all_stat():
    # read all status information and write it to disk
    global modules
    global odat
    global vlZen
    global vle1
    global filtFakt
    global p
    global heizkreis, modTVor

    for modAdr in modules:
        modIdx = modAdr - 1
        for ctrIdx in range(4):
            contr  = ctrIdx+1
            read_stat( modAdr, contr)
            #print(modAdr,contr,rxCmd)
            logstr = time.strftime('%Y%m%d_%H%M%S ')
            logstr+= "%02X%02X "%(modAdr,contr) + "HK%d "%(heizkreis) + rxCmd
            #print('store: %s'%( logstr ) )
            logwrite=logstr+'\r\n'
            odat.write( logwrite )
            if modAdr == modTVor :
                # determine Vorlauftemperatur from Zentrale
                # if modTVor == 0 it won't get here because modAdr != 0 any times
                # ":0002011a t1813989.6  W VM 61.8 RM 47.2 VE 61.8 RE 47.2 RS 41.7 "
                # "P018 E0000 FX0 M5133 A704"
                # extract temperature
                p=parse.rr_parse( logwrite )
                if len(p)  > 16 :
                    (zDateSec,hkr,module,command,control,protVer,modTStamp,summer,vlm,rlm,vle,rle,rls,ven,err,fix,tmo,tan) = p
                    if vlZen == 0.0 :
                        vle1  = vle
                        vlZen = vle
                    # low-pass filter of order 2
                    vle1  = vle *filtFakt + vle1 *(1-filtFakt)
                    vlZen = vle1*filtFakt + vlZen*(1-filtFakt)
        odat.flush()


def send_all_Tvor( vlZen ):
    global txCmd, rxCmd, modSendTvor
    #print("sende Zentraltemperaturen an:")

    # (1)
    # Geaendert 20180514: Durch eine extreme Wetterlage mit (Nacht <10deg, Tag >25deg)
    # wurde dauernd zwischen Sommer- und Winterbetrieb umgeschaltet.
    # Dies lief ueber einen laengeren Zeitraum, weshalb es auffaellt.
    # Eine Aenderung der urspruenglichen Regeln zum Verhalten der Regler ist
    # notwendig und moeglicherweise damit eine Umprogrammierung der Regler-software.
    # Als schnelle Massnahme wird die von der Zentrale an die Regler gemeldete
    # Vorlauftemperatur daher stets ueber dem Wert fuer Umschaltung zum
    # Sommerbetrieb gehalten. Diese ist derzeit auf 40 degC eingestellt.
    # Daher wird die zentrale Vorlauftemperatur auf mindestens 44 degC eingestelt.

    for modAdr in modSendTvor :
        us.ser_reset_buffer()
        tempSend = max(vlZen, 44.0)   # (1) sende mindest Temperatur, ueber Sommerbetrieb
        txCmd = mb.wrap_modbus( modAdr, 0x20, 0, ' '+str(tempSend)+' ' )
        rxCmd = us.txrx_command( txCmd )
        #print(modAdr,": ",txCmd,rxCmd)



# ----------------
# ----- main -----
# ----------------


def rr_log():
    global vlZen                # Vorlauftemperatur von Zentrale
    global heizkreis,modules,modTVor,modSendTvor,dtLog,filtFakt

    print("open network")
    err = 0
    err |= us.serial_connect()
    err |= us.ser_open()
    if( err ) :
        print("rs485 Netz = %d"%(err))
    else:
        print("rs485 Netz verbunden")
    time.sleep(1.0)

    us.ser_reset_buffer()

    print("scanning ... ");
    time.sleep(1.0)

    dtNewFile = 60.0*60.0*6.0    # sec; to make a new file
    dtLog     = 60.0* 3.0        # sec; log interval; default value
    us.ser_reset_buffer()
    timeNewFile = time.time() + dtNewFile
    ende = False
    while not ende:
        check_log_file()
        h = hkr_cfg.get_heizkreis_config(0)
        if len(h) > 5:
            (heizkreis, modules, modTVor, modSendTvor, dtLog, filtFakt) = h
        else:
            # some default values
            heizkreis   = 0
            modules     = []
            modTVor     = 0
            modSendTvor = []
            dtLog       = 180    # time interval to log a data set
            filtFakt    = 0.1
        nextTime = time.time() + dtLog
        write_all_stat()
        # (1) geaendert 20180514:
        # alt:
        # if modTVor > 0 and vlZen >= 40.0 :
        #   do not send if no T.vl measured or VL Temp. is too low
        # neu:
        if modTVor > 0 :
            # sende nur, wenn auch eine Vorlauftemperatur gemessen wurde
            send_all_Tvor( vlZen )

        while time.time() < nextTime:
            time.sleep( 1.0 )

        print(".",)
        if time.time() > timeNewFile :
            timeNewFile = time.time() + dtNewFile
            print("close log-file and start a new one")
            odat.close()
            outFileName=""

    us.ser.close()


# ----------------
# ----- main -----
# ----------------

if __name__ == "__main__" :
    while(True):
        rr_log()


