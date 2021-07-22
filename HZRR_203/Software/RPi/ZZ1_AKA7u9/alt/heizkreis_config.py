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


import numpy as np


def get_heizkreis_config( parameter = 0 ):
    # get heizkreis information from file "heizkreis.conf"
    err=0
    try:
        fhk = open("config/heizkreis.conf","r",encoding='utf-8')
    except Exception as e:
        print(e)
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
                print(e)
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
    antwort = get_heizkreis_config()
    print()
    print("="*70)
    print("test: Einlesen der Konfigurationsdaten 0: des aktiven Heizkreises")
    print("aus der datei 'heizkreis.conf' im Programmverzeichnis")
    print("-"*70)
    print(antwort)
    antwort = get_heizkreis_config(1)
    print()
    print("="*70)
    print("test: Einlesen der Konfigurationsdaten 1: des aktiven Heizkreises")
    print("aus der datei 'heizkreis.conf' im Programmverzeichnis")
    print("-"*70)
    print(antwort)
