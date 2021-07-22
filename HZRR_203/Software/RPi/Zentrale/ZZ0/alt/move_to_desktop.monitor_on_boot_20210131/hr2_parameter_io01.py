#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
hr2_parameter_io00.py
HZRR2 Parameter handling

IMPORTANT NOTE: 
===============
Files were heavily changed bei Andi and written in Classes.
It took too much time for me to understand how these work.
Thus I decided to use own code for the following functions.
It is free for someone else to integrate the new code and function
into Anids class-system later on if needed.
+ config parser .ini files is local in this file
+ serial communication is local in this file
+ parameter dialog was rewritten / worked over and 
  heavily tested due to communication errors found in installations.
  These changes may be taken over to the logging system of Andi
  to reduce or avoid RS485 collision of data packets as obtained in
  the the existing dialog.
+ The application works STAND-ALONE with no graphical interface (GUI)
  A graphical Interface may be added later, using a separate python 
  script which gets data from this module via a shared variable set
  or other means to decouple the GUI from the working part of the program.
  This is necessary because task-collisions were optained using Python
  and easy-to-use GUI systems like tkinter which obviously have problems 
  supporting several GUI-windows of different tasks.
+ the program has a terminal menu-interface for its basicc functions.
  

TASKS PERFORMED:
================
+ read, display, set parameter values of HZRR Modules
+ store parameters to file
+ read parameters from file
+ print parameters
+ compare parameters

New version Created on 07.01.2021
@author: Peter Loster (pl)

history:
hr2_parameter_io01.py  07.01.2021  pl  initial release

"""

import platform
import time
import configparser

#import copy
#import threading        as th

import hr2_variables    as hrv
#import usb_ser_b        as us
#from hr2_variables import get_cn_d
#import hz_rr_config     as cg
#import hz_rr_debug      as dbg


HR2_PARAMETER_VERSION = "1.0"


def get_hostname():    
    ''' hostname of RPi is used as identifier in "heizkreis.ini" and other "*.ini" files '''
    hostname=None     # default value is not defined;
    if platform.system() == "Linux":
        filename = "/etc/hostname"
        fd = open(filename,"r")
        hostname=fd.read().strip()
        fd.close()
    return hostname


def get_hk_param(section,hkIniFile):
    ''' read in all heizkreis parameters from ini-file to dictionary'''
    ''' section   :  get data from section '''
    ''' hkIniFile :  filename of configuration file '''
    # *** heizkreis configuration:
    hkConf  = configparser.ConfigParser()   # Heizkreis initialisation data from ini-file parser
    # read in ini-file data an treat as required:
    hkConf.read( hkIniFile )
    
    # *** hostname of RPi is used as identifier in "heizkreis.ini" and other "*.ini" files
    hkc=hkConf[section]
    hkp={}  # heizkreis parameter
    for key in hkc:
        if key=="modules" or key=="modsendtvor" or key=="regactive":
            hkp[key] = list(map(int,hkc[key].split(",")))
        else:
            hkp[key] = hkc[key]
    return hkp




def set_modparam( version ):
    ''' module parameter as they are set in Arduino Nano firmware rev. 1.0'''
    ''' version   0: Arduino Nano parameter preset values version 1.0 '''
    '''           1++: TBD'''
    if version == 0:
        modpar_d = {
            'timer1Tic'     :  10,   # uint16_t;  ms;   Timer1 period
            'tMeas'         :  120,  # uint16_t;  sec;  measuring interval  plpl
            'dtBackLight'   :  10,   # uint8_t;   min;  time to keep backlight on
            'fastMode'      :  0,    # uint8_t;         normal operation speed
            # common to all regulators
            'tv0'           :  40.0, # float;    degC;  characteristic curve
            'tv1'           :  75.0, # float;    degC;  see function
            'tr0'           :  32.0, # flaot;    degC;  characteristic()
            'tr1'           :  46.0, # flaot;    degC;  (Kennlinie)
            'tVlRxValid'    :  30,   # uint8_t;   min;  use central Vorlauf temperature until this time
            'tempZiSoll'    :  20.0, # float;    degC;  can be varied +/-4K with Zimmer Thermostat
            'tempZiTol'     :   0.5, # float;       K;  tolerance
        }
    else:
        modpar_d = None
    return modpar_d



def set_regparam( version ):
    ''' regulator parameter as they are set in Arduino Nano firmware rev. 1.0'''
    ''' version   0: Arduino Nano parameter preset values version 1.0 '''
    '''           1++: TBD'''
    if version == 0:
        regpar_d = {
            "active"      : 1,     # uint8_t;         0=inactive; 1=active (if jumper set)
            # valve motor
            "motIMin"     : 5,     # int16_6;  mA;    above: normal operation; below: open circuit 
            'motIMax'       : 70,    # int16_t;  mA;    above: mechanical limit; 2x: short circuit
            'tMotDelay'     : 80,    # int16_t;  ms;    motor current measure delay; (peak current)
            'tMotMin'       : 100,   # uint16_t; ms;    minimum motor-on time; shorter does not move
            'tMotMax'       : 40,    # uint8_t; sec;    timeout to reach limit; stop if longer
            'dtOpen'        : 28,    # uint8_t; sec;    time from limit close to limit open
            'dtClose'       : 34,    # uint8_t; sec;    time from limit open to limit close
            'dtOffset'      : 3000,  # uint16_t; ms;    time to open valve for startposition
            'dtOpenBit'     : 500,   # uint16_t; ms;    time to open valve a bit if closed is reached
            # regulation
            'pFakt'         : 0.1,   # float;  s/K;     P; dT=1K, t=0.1s => 0.1sec motor on time
            'iFakt'         : 0.0,   # float;  s/(K*s); I; dT=1K, t= 3h  => ca. 1e-4sec motor on time 
            'dFakt'         : 0.0,   # float;  s^2/K;   D; dT=1K, t=50s  => ca. 0.1sec motor on time
            #                                      (old values); tau; reach 1/e; low-pass (LP) filter
            'tauTempVl'     : 1,     # float;   sec; (60)    if <= par.tMeas: faktor=1; Low-pass off 
            'tauTempRl'     : 1,     # float;   sec; (180)  
            'tauM'          : 1,     # float;   sec; (120)   LP filter on slope
            'm2hi'          : 50.0,  # float;  mK/s; slope m too high -> pause (fast change)
            'm2lo'          : -50.0, # float;  mK/s; slope m too low  -> pause (fast change)
            'tMotPause'     : 600,   # uint16_t;sec;   time to stop motor after m2hi   
            'tMotBoost'     : 900,   # uint16_t;sec;   time to keep motor open after m2lo increase flow
            'dtMotBoost'    : 2000,  # uint16_t; ms;   motor-on time to open motor-valve for boost
            'dtMotBoostBack': 2000,  # uint16_t; ms;   motor-on time to close motor-valve after boost
            'tempTol'       : 2.0,   # float;     K;   temperature tolerance allowed for Ruecklauf
        }
    else:
        regpar_d = None
    return regpar_d    


def make_ini_file_default_nano( mode ):
    ''' make new .ini file from dictionary with default values'''
    ''' mode :  0 make only one module; 1 make all modules of heizreis'''
    hostname = get_hostname()
    hk = get_hk_param(hostname,"config/heizkreis.ini")
    modConf = configparser.ConfigParser()   # parameters for all modules
    # *** generate default data
    # generate headline information
    modConf["Info"] = {
        "forHost" : hostname ,
        "parameterVersion" : HR2_PARAMETER_VERSION
    }
    if mode == 0:
        modules=[1]
        iniFileName = "config/hr2_ModParam_Default_1mod.ini"
    else:
        modules=hk["modules"]
        iniFileName = "config/hr2_ModParam_%s_template.ini"%(hostname)
        
    modPar_d = set_modparam(0)
    regPar_d = set_regparam(0)
    for module in modules:
        modConf["MOD%d_PARAM"%(module)] = modPar_d
        for reg in range(1,4):
            modConf["MOD%d_REG%d"%(module,reg)] = regPar_d

    with open(iniFileName,"w") as configfile:
        modConf.write(configfile)


def menu_param():
    while True:
        print(40*"=")
        print("Parameter Bearbeitungsmenue")
        print(40*"-")
        print("0 Ende")
        print("1 Erzeuge einfache .ini Datei mit einem Modul und Standardwerten")
        print("2 Erzeuge .ini Datei mit Standardwerten für alle Module im Heizkreis")
        print("3 Lies Parameter von einem Modul im Heizkreis ein")
        print("4 Lies Parameter von allen Modulen im Heizkreis ein")
        print("5 Speichere Modulparameter in .ini Datei ab")
        print("6 Erzeuge Übersichtsdatei mit allen Modulparametern")
        print("7 Vergleiche Standard Parameter mit von Modulen eingelesenen Parametern")
        print("")
        print("")
        print("")
        a = int(input("Wahl:"))
        if a==0:
            return 0
        elif a==1:
            make_ini_file_default_nano(0)
            pass
        elif a==2:
            make_ini_file_default_nano(1)
            pass
        elif a==3:
            pass
        elif a==4:
            pass
        elif a==5:
            pass
        elif a==6:
            pass
        elif a==7:
            pass
        elif a==8:
            pass
    


if __name__ == "__main__":
    print("**********************************")
    print("hr2_parameter_io, revision",HR2_PARAMETER_VERSION)
    print("handle parameters")
    print("**********************************")

    #menu_param()

    print("RS485: open serial port:")
    us.ser_obj.ser_check()
    
    print("RS485: close serial port:")
    us.ser_obj.close()

