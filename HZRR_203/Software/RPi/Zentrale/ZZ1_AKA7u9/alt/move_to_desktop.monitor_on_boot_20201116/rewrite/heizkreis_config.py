#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
HZ-RR012 Heizkries Parameter

Created on 11.01.2017
@author: Peter Loster (pl)

history:

# Informationen zum aktuellen Heizkreis
# wird von allen Programmen verwendet
# Daten sind in der Datei "heizkreis.conf"
# Versionen':
# 0.1  11.01.17  pl  erstellt, mit Mod. Nr. und aktiven Modulen
# 0.2  16.01.17  pl  erweitert um Modul_Tvor; #-Zeilen verwerfen
# 0.3  16.02.17  pl  erweitert um 1: (siehe unten)

"""

import os
import subprocess
import numpy as np

import hz_rr_config as cg
import hz_rr_debug as dbg

global cg
cg = cg.conf_obj
dbg = dbg.Debug(1)
#cg.conf(cg.configfile_n)

            # heizkreis   modules     Modul_Tvor  modSendTvor interval filterfaktor regActive TVorlAendWarn TVorlAendAlarm TRueckAendWarn TRueckAendAlarm TRueckDeltaPlus
            # TRueckDeltaMinus venTravelWarn venTravelWarn venTravelAlarm
def set_heizkreis_config( parameter = "heizkreis", value = 3, setonusb = 1 ):
    global cg
    confpath=cg.r("system","confPath_local")
    if (setonusb == 1): confpath= cg.r("system","confPath_USB")

    dbg.m("write path using ", confpath)
    # get heizkreis information from file "heizkreis.conf"
    err=0
    try:
        fhk = open(confpath,"r",encoding='utf-8')
    except Exception as e:
        dbg.m("Exception:", str(e))
        err = 1
    else:
        hks = []
        done = 0
        for line in fhk:
            if line[0] != "#":
                if (done == 0):
                    if (line.find(parameter)  != -1):
                        line = parameter + " " + str(value) + "\r"
                        done =1
            hks.append(line)
        fhk.close()

    try:
        a=os.path.isdir("config") #del old config file
        #a = subprocess.call("rm -r " + confpath, shell=True) # try to remove existing files - will be replaced by new ones
        #dbg.m("rm +r = " + str(a))
        os.remove(confpath)

    except Exception as e:
        dbg.m(e)
        err = 2

    # open write and close file
    try:
        n = open(confpath,"x",encoding='utf-8')
        for line in hks:
            #dbg.m(line)
            n.write(line)

    except Exception as e:
        dbg.m("Exception:", str(e))
        err = 2
    
    try:
        n.close()
    
    except Exception as e:
        dbg.m("Exception:", str(e))
        err = 3

    #done?!

def get_heizkreis_config( parameter = 0, readfromusb = 1 ):
    global cg
    confpath=cg.r("system","confPath_local")
    if (readfromusb == 1): 
        confpath= cg.r("system","confPath_USB")
        #confpath="D:\\coding\\move_to_desktop.monitor_on_boot\\config\\heizkreis.conf"

    dbg.m("read path using ", confpath)

    err=0
    try:
        fhk = open(confpath,"r",encoding='utf-8')
    except Exception as e:
        dbg.m("Exception:", str(e))
        err = 1
    else:
        hks = []
        for line in fhk:
            if line[0] != "#":
                # no comment
                hks.append(line)
        fhk.close()

        try:
            # Nr. des Heizkreises
            heizkreis = int([hkline for hkline in hks if "heizkreis" in hkline][0].split()[1])
        except Exception as e:
            err = 2

        try:
            # Nummern einzulesender Module
            m = [ hkline for hkline in hks if "modules" in hkline][0].split()[1]
            modules = np.array( m.split(","), int )
        except Exception as e:
            err = 3

        try:
            # Modul mit zentraler Vorlauftemperatur; 0 falls es fehlt
            modTRef = int([hkline for hkline in hks if "Modul_Tvor" in hkline][0].split()[1])
        except Exception as e:
            err = 4

        try:
            # Module an welche zentrale Vorlauftemperaturen gesendet werden
            m = [ hkline for hkline in hks if "modSendTvor" in hkline][0].split()[1]
            modSendTvor = np.array( m.split(","), int )
        except Exception as e:
            err = 5

        try:
            # Intervall zum Abruf der Daten von den Modulen in Sekunden:
            dtLog = int([hkline for hkline in hks if "interval" in hkline][0].split()[1])
        except Exception as e:
            err = 6

        try:
            # Filter faktor zur Bewertung der neuen Messwertes zentrale Vorlauftemperatur
            filtFakt = float([hkline for hkline in hks if "filterfaktor" in hkline][0].split()[1])
        except Exception as e:
            err = 7

        if parameter == 1 :
            pass
            try:
                # Anzahl aktiver Regler in jedem Modul
                m = [ hkline for hkline in hks if "regActive" in hkline][0].split()[1]
                regActive = np.array( m.split(","), int )
            except Exception as e:
                dbg.m(e)
                err = 8

            try:
                #  Aenderung in der Temperatur von Vorlauf/Stunde:
                TVorlAendWarn = float([hkline for hkline in hks if "TVorlAendWarn" in hkline][0].split()[1])
            except Exception as e:
                err = 9

            try:
                #
                TVorlAendAlarm = float([hkline for hkline in hks if "TVorlAendAlarm" in hkline][0].split()[1])
            except Exception as e:
                err = 10

            try:
                #  Aenderung in der Temperatur von Ruecklauf/Stunde:
                TRueckAendWarn = float([hkline for hkline in hks if "TRueckAendWarn" in hkline][0].split()[1])
            except Exception as e:
                err = 11

            try:
                #
                TRueckAendAlarm = float([hkline for hkline in hks if "TRueckAendAlarm" in hkline][0].split()[1])
            except Exception as e:
                err = 12

            try:
                #
                TRueckDeltaPlus = float([hkline for hkline in hks if "TRueckDeltaPlus" in hkline][0].split()[1])
            except Exception as e:
                err = 13

            try:
                #
                TRueckDeltaMinus = float([hkline for hkline in hks if "TRueckDeltaMinus" in hkline][0].split()[1])
            except Exception as e:
                err = 14

            try:
                #
                venTravelWarn = float([hkline for hkline in hks if "venTravelWarn" in hkline][0].split()[1])
            except Exception as e:
                err = 15

            try:
                #
                venTravelAlarm = float([hkline for hkline in hks if "venTravelAlarm" in hkline][0].split()[1])
            except Exception as e:
                err = 16

    dbg.m("done reading all: (heizkreis=", heizkreis, ")")

    if err > 0:
        return(["err",err])
    else:
        if parameter == 0:
            rv0=(heizkreis, modules, modTRef, modSendTvor, dtLog, filtFakt)
            return rv0
        if parameter == 1:
            rv1=(regActive,TVorlAendWarn,TVorlAendAlarm,\
                 TRueckAendWarn,TRueckAendAlarm,\
                 TRueckDeltaPlus,TRueckDeltaMinus,\
                 venTravelWarn,venTravelAlarm)
            return rv1


# ----------------
# ----- main -----
# ----------------



# test:
if __name__ == "__main__" :
    set_heizkreis_config("heizkreis",2,1)
    antwort = get_heizkreis_config(0,1)
    dbg.m()
    dbg.m("="*70)
    dbg.m("test: Einlesen der Konfigurationsdaten 0: des aktiven Heizkreises")
    dbg.m("aus der datei 'heizkreis.conf' im Programmverzeichnis")
    dbg.m("-"*70)
    dbg.m(str(antwort))
    antwort = get_heizkreis_config(1)
    dbg.m()
    dbg.m("="*70)
    dbg.m("test: Einlesen der Konfigurationsdaten 1: des aktiven Heizkreises")
    dbg.m("aus der datei 'heizkreis.conf' im Programmverzeichnis")
    dbg.m("-"*70)
    dbg.m(str(antwort))
