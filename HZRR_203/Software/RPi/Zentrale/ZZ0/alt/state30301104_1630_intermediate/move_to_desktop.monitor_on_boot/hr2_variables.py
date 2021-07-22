#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# variables combined in classes

PROT_REV = "b"      # protocol revision for hzrr200


class Status:
    rxCmd      = ""      # received command-string
    rxAdr      = 0
    rxCmdNr    = 0
    rxSender   = 0
    rxSubAdr   = 0
    rxProt     = 0
    rxMillis   = 0
    rxMotConn  = 0
    rxMotImA   = 0
    jumpers    = 0

st = Status()


# status variables for logging
cn2={"SN":0,"VM":0,"RM":0,"VE":0,"RE":0,"RS":0,"PM":0} # command names
cn4={"ER":0,"FX":0,"MT":0,"NL":0} # command names



# Parameter for each regulator
#   active, motIMin, motIMax, tMotDelay, tMotMin, tMotMax,
#   dtOpen, dtClose, dtOffset, tMotTotal, nMotLimit,
#   pFakt, iFakt, dFakt, tauTempVl, tauTempRl, tauM, m2hi, m2lo,
#   tMotPause, tMotBoost, dtMotBoost, dtMotBoostBack
parReg = {
    # valve motor
    "active":        0,     # uint8_t;   0=inactive; 1=Ruecklauf;
    "motIMin":       6,     # int16_t;   mA;   above: normal operation; below: open circuit 
    "motIMax":      71,     # int16_t;   mA;   above: mechanical limit; 2x: short circuit
    "tMotDelay":    81,     # int16_t;   ms;   motor current measure delay; (peak current)
    "tMotMin":     101,     # uint16_t;  ms;   minimum motor-on time; shorter does not move
    "tMotMax":      41,     # uint8_t;   sec:  timeout to reach limit; stop if longer
    "dtOpen":       29,     # uint8_t;   sec;  time from limit close to limit open
    "dtClose":      35,     # uint8_t;   sec;  time from limit open to limit close
    "dtOffset":   3001,     # uint16_t;  ms;   time to open valve for startposition#
    "dtOpenBit":   500,     # uint16_t;  ms;   time to open valve a bit when close-limit reached
    "tMotTotal":   0.1,     # float;     sec;  total motor-on time 
    "nMotLimit":     1,     # uint16_t;  1;    count of limit-drives of motor
    # regulation
    "pFakt":       0.11,    # float;     s/K;  P-factor; motor-on time per Kelvin diff.
    "iFakt":       0.01,    # float;     1/K;  I-factor;
    "dFakt":       0.01,    # float;     s^2/K D-factor; 
    "tauTempVl":  300.1,    # float;     sec;  reach 1/e; low-pass (LP) filter Vorlauf
    "tauTempRl":  180.1,    # float;     sec;  reach 1/e; LP filter Ruecklauf (RL)<
    "tauM":       120.1,    # float;     sec;  reach 1/e; LP filter slope m
    "m2hi":       40.1,     # float;     mK/s; up-slope; stop motor if above for some time
    "m2lo":       -40.1,    # float;     mK/s; down-slope; open valve a bit
    "tMotPause":  601,      # uint16_t;  sec;  time to stop motor after m2hi
    "tMotBoost":  901,      # uint16_t;  sec;  time to keep motor open after m2lo increase flow
    "dtMotBoost":  2001,    # uint16_t;  ms;   motor-on time to open motor-valve for boost
    "dtMotBoostBack": 2001, # uint16_t;  ms;   motor-on time to close motor-valve after boost 
    "tempTol":     2.1,     # float;     K;    temperature tolerance allowed for Ruecklauf
    }

# Parameter for the module

'''
// calculate Ruecklauf temperature from given Vorlauf temperature
// following a polygon shaped characteristic curve (Kennlinie)
// determined by a lint through the points from (tv0,tr0) to (tv1,tr1) 
//
// tr1|- - - - - - - +-----
//    |             /:
//    |           /  :
//  y |- - - - -+    :
//    |       / :    :
// tr0|----+/   :    :
//    |    :    :    :
//    |    :    :    :
//    +---------+----------
//       tv0   tv   tv1
// 
'''
#timer1Tic,tMeas,dtBackLight,tv0,tv1,tr0,tr1,tVlRxValid,tempZiSoll,tempZiTol

parameter = {
    "timer1Tic":      11,   # uint16_t; ms;    Interrupt heartbeat of Timer1
    "tMeas":          61,   # uint16_t; sec;   measuring interval
    "dtBackLight":    11,   # uint8_t;  min;   LCD time to switch off backlight
    # characteristic curve (Kennlinie)
    "tv0":          40.1,   # float;    degC;  calculate Ruecklauf temperature 
    "tv1":          75.1,   # float;    degC;  from characteristic curve
    "tr0":          32.1,   # float;    degC;  see above
    "tr1":          46.1,   # float;    degC;
    "tVlRxValid":     16,   # uint8_t;  min;    st.tempVlRx is valid this time;
    # regulator 1: special Zimmer temperature if active==2:
    "tempZiSoll":   20.1,   # float; degC;  Zimmer temp. soll; +/-4K with room Thermostat
    "tempZiTol":     0.6,   # float;degC:  toleracne for room-temperature
    "r":           [parReg for i in range(3)] # three sets of regulator parameters
    }

# --------------------------------------------------------------
parameters = [parameter for i in range(31)]   #up to 31 modules
# --------------------------------------------------------------
# ATTENTION:
# access module nr. 30 parameter e.g.:
#     parameters[30-1]['tMeas']
# access regulator 0 (subAdr 1) parameter of module nr. 30 e.g.:
#     parameters[30-1]['r'][0]["tMotTotal"]
# --------------------------------------------------------------

def parameters_zero():
    for n in range(31):
        par = parameters[n]
        for n in par:
            if n != "r":
                par[n] = 0
            else:
                for i in range(3):
                    spar=par["r"][i]
                    for n in spar:
                        spar[n]=0





import platform
import sys

pyVers = platform.python_version()
if pyVers < "3.6":
    print("must be at least Python 3.6")
    sys.exit(1)


