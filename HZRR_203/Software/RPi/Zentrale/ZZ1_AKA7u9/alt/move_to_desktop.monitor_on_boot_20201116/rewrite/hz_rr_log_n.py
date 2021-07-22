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
hz_rr_log.py         27.07.2018  pl/bd  Sende permanent 20 Grad -> Sommerbetrieb
                     NUR VORLAEUFIG !!!
hz_rr_log.py         22.10.2019  pl/bd Winterbetrieb wieder aktiviert
hz_rr_log.py         30.11.2019  pl    Statusausgabe '.' jetzt ohne Zeilenschaltung
"""

import sys
import time
import os
import glob
import numpy as np
import usb_ser_b as us
import modbus_b  as mb
import hr2_variables as hrv
import heizkreis_config as hkr_cfg
import rr_parse as parse
import hz_rr_config as cg
import hz_rr_debug as dbg

def wait(s) :
    pass
    #print(s)
    #time.sleep(2.0)

class Log():
    modules= odat= vlZen= vle1= filtFakt= heizkreis= \
        modTVor= p= outFileName= locPath= modAdr= cn2= cn4= \
        txCmd= rxCmd= modSendTvor = None
    pltpath     =   cg.conf_obj.r('system','logPlotPath')
    loggerpath  =   cg.conf_obj.r('system','logStartScriptPath')
    lmdname     =   cg.conf_obj.r('system','logMonitorDirectPath')
    log_on_usb  =   cg.conf_obj.r('system','logOnUSB')
    locPath     =   cg.conf_obj.r('system','logPath_local')
    dbg = dbg.Debug(1)

    #windows: locPath="D:\\coding\\move_to_desktop.monitor_on_boot\\log\\"
    if log_on_usb:
        locPath = cg.conf_obj.r('system','logPath_USB')
    dbg.m("logging to:", locPath)
    fn=time.strftime(locPath+cg.conf_obj.r('system','logFileNameMask'))

    dbg.m("new file:",fn)
    try:   
        odat = open(fn,'w')
    except Exception as e:
        dbg.m("error opening file:", fn, "\r","err:",e)
    odat.close()

    # some initial values
    filtFakt= 0.1    # Filter 2. Ordnung; filtFakt = Bewertung des neuen Wertes
    vlZen   = 0.0       # temperature from Zentrale Vorlauf; 0 -> no temperature
    vle1    = 0.0       # initial value
    modAdr  = 4
    subAdr  = 1


    def check_log_file(self):
        x = self.outFileName
        if x == "" \
        or self.odat.closed : # open new file
            self.outFileName=self.locPath+'logHZ-RR_'+time.strftime('%Y%m%d_%H%M%S.dat')
            self.odat = open(self.outFileName, 'w' )

    def write_all_stat(self):
        for self.modAdr in self.modules:
            self.modIdx = self.modAdr - 1
            for self.ctrIdx in range(3):
                self.contr  = self.ctrIdx+1
                x = us.ser_obj.read_stat(self.modAdr, self.contr)
                #while (x == 8): #serbus busy!
                #    x = us.ser_obj.read_stat(self.modAdr,self.subAdr)
                #    time.sleep(0.5)
                
                
                #print(modAdr,contr,rxCmd)
                logstr = time.strftime('%Y%m%d_%H%M%S ')
                self.dbg.m(str(hrv.st))
                #20191016_075934 0901 HK2 :0002091a t4260709.0  S VM 46.0 RM 42.5 VE 20.0 RE 42.5 RS 32.2 P074 E0000 FX0 M2503 A135
                logstr+= "%02X%02X "%(self.modAdr,self.contr) + "HK%d "%(self.heizkreis) + ":" + str(x)
                self.dbg.m('store: %s'%( logstr ) )
                logwrite=logstr+'\r\n'
                self.odat.write( logwrite )
                if self.modAdr == self.modTVor :
                    # determine Vorlauftemperatur from Zentrale
                    # if modTVor == 0 it won't get here because modAdr != 0 any times
                    # ":0002011a t1813989.6  W VM 61.8 RM 47.2 VE 61.8 RE 47.2 RS 41.7 "
                    # "P018 E0000 FX0 M5133 A704"
                    # extract temperature
                    p=parse.rr_parse( logwrite )
                    if len(p)  > 16 :
                        (self.zDateSec,self.hkr,self.module,self.command,self.control, \
                            self.protVer,self.modTStamp,self.summer,self.vlm,self.rlm,self.vle,self.rle, \
                            self.rls,self.ven,self.err,self.fix,self.tmo,self.tan) = p
                        if self.vlZen == 0.0 :
                            self.vle1  = self.vle
                            self.vlZen = self.vle
                        # low-pass filter of order 2
                        self.vle1  = self.vle *self.filtFakt + self.vle1 *(1-self.filtFakt)
                        self.vlZen = self.vle1*self.filtFakt + self.vlZen*(1-self.filtFakt)
            self.odat.flush()

    def send_all_Tvor( self, vlZen ):
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
        for self.modAdr in self.modSendTvor :
            us.ser_obj.ser_reset_buffer()
            tempSend = max(vlZen, 44.0)   # (1) sende mindest Temperatur, ueber Sommerbetrieb
            # heisser Sommer; Regler pendeln mit obiger Einstellung
            # zwischen Sommer- und Winterbetrieb
            # Versuch einer Abhilfe durch dauerndes Sommerbetrieb Schalten
            # es wird konstant 20.0 Grad Vorlauf gesendet (unter 30 Grad ist Sommer)        
            # FIXME        
            #tempSend = 20.0   # (1) sende mindest Temperatur, ueber Sommerbetrieb
            self.txCmd = mb.wrap_modbus( self.modAdr, 0x20, 0, ' '+str(tempSend)+' ' )
            self.rxCmd = us.ser_obj.txrx_command( self.txCmd )
            #print(modAdr,": ",txCmd,rxCmd)

    def rr_log(self):
        x = us.ser_obj.read_stat(self.modAdr,self.subAdr)
        #while (x == 8): #serbus busy!
        #    x = us.ser_obj.read_stat(self.modAdr,self.subAdr)
        #    time.sleep(0.5)

        time.sleep(1.0)

        dtNewFile = 60.0*60.0*6.0    # sec; to make a new file
        dtLog     = 10#60.0* 3.0        # sec; log interval; default value
        
        us.ser_obj.ser_reset_buffer()
        timeNewFile = time.time() + dtNewFile
        ende = False

        while not ende:
            self.check_log_file()
            h = hkr_cfg.get_heizkreis_config(0)
            if len(h) > 5:
            #    (heizkreis, modules, modTVor, modSendTvor, dtLog, filtFakt) = h
                (self.heizkreis, self.modules, self.modTVor, self.modSendTvor, self.dtLog, self.filtFakt) = h
            else:
            #   # some default values
            #   heizkreis   = 0
            #   modules     = []
            #   modTVor     = 0
            #   modSendTvor = []
            #   dtLog       = 180    # time interval to log a data set
            #   filtFakt    = 0.1
                self.heizkreis = 0
                self.modules = 0
                self.modTVor = 0
                self.modSendTvor = []
                self.dtLog = 180
                self.filtFakt = 0.1

            nextTime = time.time() + dtLog
            self.write_all_stat()
            # (1) geaendert 20180514:
            # alt:
            # if modTVor > 0 and vlZen >= 40.0 :
            #   do not send if no T.vl measured or VL Temp. is too low
            # neu:
            
            while (time.time() < nextTime):
                time.sleep( 1.0 )

            #self.dbg.m(".",ende="")
            if time.time() > timeNewFile :
                timeNewFile = time.time() + dtNewFile
                self.dbg.m("close log-file and start a new one")
                self.odat.close()
                self.outFileName=""

        #us.ser_obj.ser.close()

log_obj = Log()



if __name__ == "__main__" :
    print("*****************************")
    print("hz-rr-log")
    print("creating logfile")
    print("*****************************")

    lg = Log()
    print(lg.modules)
    #us.ser_obj.ser_check()

    while(True):
        lg.rr_log()
    
    us.ser_obj.close()


