#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# variables combined in classes


#import hz_rr_debug as dbg

PROT_REV = "b"      # protocol revision for hzrr200


jumpers =0
rxMillis=0

__x = -1
cn2             =   {"SN":__x,"VM":__x,"RM":__x,"VE":__x,"RE":__x,"RS":__x,"PM":__x} # command names
cn4             =   {"ER":__x,"FX":__x,"MT":__x,"NL":__x} # command names
__x = 0
_default_cn2    =   {"SN":__x,"VM":__x,"RM":__x,"VE":__x,"RE":__x,"RS":__x,"PM":__x} # command names
_default_cn4    =   {"ER":__x,"FX":__x,"MT":__x,"NL":__x} # command names
__x = -2
cn2_ser         =   {"SN":__x,"VM":__x,"RM":__x,"VE":__x,"RE":__x,"RS":__x,"PM":__x} # command names
cn4_ser         =   {"ER":__x,"FX":__x,"MT":__x,"NL":__x} # command names
__x = -3
cn2_log         =   {"SN":__x,"VM":__x,"RM":__x,"VE":__x,"RE":__x,"RS":__x,"PM":__x} # command names
cn4_log         =   {"ER":__x,"FX":__x,"MT":__x,"NL":__x} # command names
__x = -4
cn2_mon         =   {"SN":__x,"VM":__x,"RM":__x,"VE":__x,"RE":__x,"RS":__x,"PM":__x} # command names
cn4_mon         =   {"ER":__x,"FX":__x,"MT":__x,"NL":__x} # command names

class Status:
    global cn2, cn2_ser, cn2_mon, cn2_log, cn4, cn4_ser, cn4_mon, cn4_log

    def __init__(self):
        self.rxCmd       = ""      # received command-string
        self.rxAdr       = 0
        self.rxCmdNr     = 0
        self.rxSender    = 0
        self.rxSubAdr    = 0
        self.rxProt      = 0
        self.rxMillis    = 0
        self.rxMotConn   = 0
        self.rxMotImA    = 0
        self.jumpers     = 0
        self.mon_rx_cpy  = ""
        self.log_vm_cpy  = getattr(cn2_log,'VM',0)
        #self.dbg = dbg.Debug(1)  # *at* removed - prduces error with "hz_rr__config.py"
        
        

st = Status()

# status variables for logging

def get_cn(m=""):
    #print("[GET_CN]:",m)
    global cn2_mon,cn4_mon,cn2_log,cn4_log,cn2_ser,cn4_ser,cn2,cn4
    if (m=='m'): return (cn2_mon,cn4_mon)
    if (m=='s'): return (cn2_ser,cn4_ser)
    if (m=='l'): return (cn2_log,cn4_log)
    return (cn2,cn4)

def set_cn(m="m"):
    global cn2_mon,cn4_mon,cn2_log,cn4_log,cn2_ser,cn4_ser,cn2,cn4
    #s_cn2 = str(cn2)#[:50]
    #s_cn4 = str(cn4)#[:50]
    #s_cn2m= str(cn2_mon)#[:50]
    #s_cn4m= str(cn4_mon)#[:50]
    #s_cn2s= str(cn2_ser)#[:50]
    #s_cn4s= str(cn4_ser)#[:50]
    #s_cn2l= str(cn2_log)#[:50]
    #s_cn4l= str(cn4_log)#[:50]

    #print("[set_cn]INIT:",m,"//cn2:",s_cn2,"//cn4:",s_cn4)
    #print("[set_cn]cn2_ser",m,"//cn2:",s_cn2,"//cn4:",s_cn4)
    if (m=='m'):
        #print("[set_cn]cn2_mon-BEFORE:","s_cn2m:",s_cn2m,"//s_cn4m:",s_cn4m)
        cn2_mon.update(cn2_ser)
        cn4_mon.update(cn4_ser)
        while (cn2_mon != cn2_ser and cn4_mon != cn4_ser): pass #wait for update to finish
        reset_cn('s')
        #s_cn2m= str(cn2_mon)#[:50]
        #s_cn4m= str(cn4_mon)#[:50]
        #print("[set_cn]cn2_mon-AFTER:","s_cn2m:",s_cn2m,"//s_cn4m:",s_cn4m)

    if (m=='s'):
        #print("[set_cn]cn2_ser-BEFORE:","s_cn2s:",s_cn2s,"//s_cn4s:",s_cn4s)
        cn2_ser.update(cn2)
        cn4_ser.update(cn4)
        while (cn2_ser != cn2 and cn4_ser != cn4): pass #wait for update to finish
        reset_cn('')
        #s_cn2s= str(cn2_ser)#[:50]
        #s_cn4s= str(cn4_ser)#[:50]
        #print("[set_cn]cn2_ser-AFTER:","s_cn2s:",s_cn2s,"//s_cn4s:",s_cn4s)

    if (m=='l'):
        #print("[set_cn]cn2_log-BEFORE:","s_cn2l:",s_cn2l,"//s_cn4l:",s_cn4l)
        cn2_log.update(cn2_ser)
        cn4_log.update(cn4_ser)
        while (cn2_log != cn2_ser and cn4_log != cn4_ser): pass #wait for update to finish
        reset_cn('s')
        #s_cn2l= str(cn2_log)#[:50]
        #s_cn4l= str(cn4_log)#[:50]
        #print("[set_cn]cn2_log-AFTER:","s_cn2l:",s_cn2l,"//s_cn4l:",s_cn4l)

    #reset_cn(0)

def reset_cn(m="m"):
    #print("[RESET_CN]:",m)
    global cn2_mon,cn4_mon,cn2_log,cn4_log,cn2_ser,cn4_ser,cn2,cn4
    if (m=='m'):
        cn2_mon.update(_default_cn2)
        cn4_mon.update(_default_cn4)
        while (cn2_mon != _default_cn2 and cn4_mon != _default_cn4): pass #wait for update to finish
    if (m=='s'):
        cn2_ser.update(_default_cn2)
        cn4_ser.update(_default_cn4)
        while (cn2_ser != _default_cn2 and cn4_ser != _default_cn4): pass #wait for update to finish

    if (m=='l'):
        cn2_log.update(_default_cn2)
        cn4_log.update(_default_cn4)
        while (cn2_log != _default_cn2 and cn4_log != _default_cn4): pass #wait for update to finish

    else:
        cn2.update(_default_cn2)
        cn4.update(_default_cn4)
        while (cn2 != _default_cn2 and cn4 != _default_cn4): pass #wait for update to finish


def get_cn_d():
    global _default_cn2, _default_cn4
    return (_default_cn2, _default_cn4)

# *** Parameter for each regulator
#   active, motIMin, motIMax, tMotDelay, tMotMin, tMotMax,
#   dtOpen, dtClose, dtOffset, tMotTotal, nMotLimit,
#   pFakt, iFakt, dFakt, tauTempVl, tauTempRl, tauM, m2hi, m2lo,
#   tMotPause, tMotBoost, dtMotBoost, dtMotBoostBack
parReg = {
    # valve motor
    "active":        1,     # uint8_t;   0=inactive; 1=Ruecklauf;
    "motIMin":       6,     # int16_t;   mA;   above: normal operation; below: open circuit 
    "motIMax":      71,     # int16_t;   mA;   above: mechanical limit; 2x: short circuit
    "tMotDelay":    81,     # int16_t;   ms;   motor current measure delay; (peak current)
    "tMotMin":     101,     # uint16_t;  ms;   minimum motor-on time; shorter does not move
    "tMotMax":      41,     # uint8_t;   sec:  timeout to reach limit; stop if longer
    "dtOpen":       29,     # uint8_t;   sec;  time from limit close to limit open
    "dtClose":      35,     # uint8_t;   sec;  time from limit open to limit close
    "dtOffset":   3001,     # uint16_t;  ms;   time to open valve a bit when close-limit reached#
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
    "r":           [parReg for i in range(4)] # three sets of regulator parameters
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


