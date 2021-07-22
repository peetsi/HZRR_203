#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# parse_answer

from hr2_variables import *


def get_command_list():
    ''' split ',' separated values from st.rxCmd in list '''
    l = st.rxCmd.split(",")
    while l[0] == '' :
        l.pop(0)
    while l[-1] == '' :
        l.pop()
    return l



def parse_answer():
    # ":0002021b VM25.7 RM25.8 VE0.0 RE0.0 RS0.0 PM88 0A003F"
    # where:
    # st.rxCmd = "0002021b VM25.7 RM25.8 VE0.0 RE0.0 RS0.0 PM88";
    # csum="0A00"; lrc="3F"
    print("parse_answer: st.rxCmd=",st.rxCmd)
    if st.rxCmd=="":
        return
    st.rxAdr    = int(st.rxCmd[0:2],16)
    st.rxCmdNr  = int(st.rxCmd[2:4],16)
    st.rxSender = int(st.rxCmd[4:6],16)
    st.rxSubAdr = int(st.rxCmd[6:7])
    st.rxProt   = st.rxCmd[7:8]
    
    st.rxCmd = st.rxCmd[9:-7] # remove address header and checksum trailer

    modAdr = st.rxSender
    #subAdr = st.rxSubAdr

    #print("parse_answer: truncated st.rxCmd=",st.rxCmd)
    
    #print("adr=",st.rxAdr)
    #print("cmdNr=",st.rxCmdNr)
    #print("Sender=",st.rxSender)
    #print("SubAdr=",st.rxSubAdr)
    #print("Prot=",st.rxProt)
    #print("=",st.rx)
    
    
    if st.rxProt != PROT_REV:
        return
    
    elif st.rxCmdNr == 1 :  # ping command
        if "ACK" in st.rxCmd :
            return True
        
    elif st.rxCmdNr == 2 :  # read status values part 1
        if st.rxSubAdr == 0 :
            if "ACK" in st.rxCmd :   # "ACK" - no data to be sent
                return True
        elif st.rxSubAdr in [1,2,3]:
            # "VM25.7 RM25.8 VE0.0 RE0.0 RS0.0 PM88"
            # result is in dictionary cn2, rest see command 4
            #
            #// no winter- or summer operation -> omitted in type b protocol
            #// VM RM: Vl/Rl temp. measured
            #// VE RE: Vl/Rl temp. effectively used for regulation
            #// RS:    Rl temp. soll
            #// PM:     Permille motor-valve setting; 0=closed, 999=open
            
            l = st.rxCmd.strip().split(",")
            while(l[0]==''):
                l.pop(0)
            while(l[-1]==''):
                l.pop()
            for v in l:
                #print(v)
                if v == "S" or v == "W" :
                    cn2["SN"] = v
                    #print(cn2)
                else:
                    # von plpl eingefuegt:
                    try:
                        nm = v[0:2]
                        cn2[nm]=float(v[2:])
                    except Exception as e:
                        # do nothing
                        pass
            #print(cn2)
            return True

    # command 3 not implemented in rev hr2 (was in hr010)
    # sends regulator parameter -> new command
    
    elif st.rxCmdNr == 4 :  # read status values part 2
        if st.rxSubAdr == 0 :
            # "ACK" - no data received
            if "ACK" in st.rxCmd :
                return True
        elif st.rxSubAdr in [1,2,3]:
            l = st.rxCmd.strip().split(",")
            while(l[0]==''):
                l.pop(0)
            while(l[-1]==''):
                l.pop()
            for v in l:
                nm = v[0:2]     # dictionary name (=index)
                # added plpl:
                if nm == "ER":  # value is in hex
                    cn4[nm] = int(v[2:],16)
                else:           # other values can be handled as float
                    cn4[nm]=float(v[2:])
                    if (v == "tMotTotal") or (v == "nMotLimit"):
                        # store also in parameters
                        parameters[modAdr-1]['r'][st.rxSubAdr-1][v] = float(v[2:])
            return True
    
    elif st.rxCmdNr == 5:  # read parameter: module / reg.part 1
        #timer1Tic,tMeas,dtBackLight,tv0,tv1,tr0,tr1,
        #tVlRxValid,tempZiSoll,tempTolRoom
        l = get_command_list()
        
        par = parameters[modAdr-1]
        if st.rxSubAdr == 0:
            # read timer1Tic,tMeas,dtBackLight,
            #   tv0,tv1,tr0,tr1,tVlRxValid,tempZiSoll,tempZiTol
            for n in par:
                if n == "r":
                    continue
                par[n]=l.pop(0)
            return True
    
        elif st.rxSubAdr in [1,2,3]:
            # read:
            #   active, motIMin, motIMax, tMotDelay, tMotMin, tMotMax,
            #   dtOpen, dtClose, dtOffset
            pr = par["r"][st.rxSubAdr-1]
            start=False
            for n in pr:          # start at begin of directory
                pr[n]=l.pop(0)
                if l == []:     # last item provided
                    break
            return True

    elif st.rxCmdNr == 6:  # read parameter: module / reg.part 2
        print("parse_answer %02x: st.rxCmd = %s"%(st.rxCmdNr,st.rxCmd))
        if st.rxSubAdr == 0:
            # "ACK" - no data available
            if "ACK" in st.rxCmd :
                return True
    
        elif st.rxSubAdr in [1,2,3]:
            # "tMotTotal" and "nMotLimit" are not transferred here
            # they are received with command nr. 4 as "MT" and "NL"
            # read:
            #   pFakt, iFakt, dFakt, tauTempVl, tauTempRl, tauM
            l = get_command_list()
            par = parameters[modAdr-1]
            pr = par["r"][st.rxSubAdr-1]
            start=False
            for n in pr:
                if n == "pFakt":  # first item to be filled
                    start=True
                if start :
                    pr[n]=l.pop(0)
                    if l == []:     # last item provided
                        break
            return True


    elif st.rxCmdNr == 7:  # read parameter: module / reg.part 3
        print("parse_answer %02x: st.rxCmd = %s"%(st.rxCmdNr,st.rxCmd))
        if st.rxSubAdr == 0:
            # "ACK" - no data available
            if "ACK" in st.rxCmd :
                return True
    
        elif st.rxSubAdr in [1,2,3]:
            # read:
            #   m2hi, m2lo,
            #   tMotPause, tMotBoost, dtMotBoost, dtMotBoostBack
            l = get_command_list()
            par = parameters[modAdr-1]
            pr = par["r"][st.rxSubAdr-1]
            start = False
            for n in pr:
                if n == "m2hi":  # first item to be filled
                    start=True
                if start :
                    pr[n]=l.pop(0)
                    if l == []:     # last item provided
                        break
            return True


    elif st.rxCmdNr == 0x20 :  # Zentrale Vorlauftemperatur received
        print("parse_answer %02x: st.rxCmd = %s"%(st.rxCmdNr,st.rxCmd))
        if "ACK" in st.rxCmd :
            return True
        

    elif st.rxCmdNr == 0x22 :  # setze parameter
        print("parse_answer %02x: st.rxCmd = %s"%(st.rxCmdNr,st.rxCmd))
        if "ACK" in st.rxCmd :
            return True
        

    elif st.rxCmdNr == 0x23 :  # setze parameter
        print("parse_answer %02x: st.rxCmd = %s"%(st.rxCmdNr,st.rxCmd))
        if "ACK" in st.rxCmd :
            return True


    elif st.rxCmdNr == 0x24 :  # setze parameter
        print("parse_answer %02x: st.rxCmd = %s"%(st.rxCmdNr,st.rxCmd))
        if "ACK" in st.rxCmd :
            return True
        
            
    elif st.rxCmdNr == 0x25 :  # set special parameters
        print("parse_answer %02x: st.rxCmd = %s"%(st.rxCmdNr,st.rxCmd))
        if "ACK" in st.rxCmd :
            return True

    elif st.rxCmdNr == 0x30 :  # reset all parameters to factory settings
        print("parse_answer %02x: st.rxCmd = %s"%(st.rxCmdNr,st.rxCmd))
        if "ACK" in st.rxCmd :
            return True

    elif st.rxCmdNr == 0x31 :  # move valve; time and direction
        print("parse_answer %02x: st.rxCmd = %s"%(st.rxCmdNr,st.rxCmd))
        if "ACK" in st.rxCmd :
            return True

    elif st.rxCmdNr == 0x34 :  # set normal operation
        print("parse_answer %02x: st.rxCmd = %s"%(st.rxCmdNr,st.rxCmd))
        if "ACK" in st.rxCmd :
            return True

    elif st.rxCmdNr == 0x35 :  # set regulator active/inactive
        print("parse_answer %02x: st.rxCmd = %s"%(st.rxCmdNr,st.rxCmd))
        if "ACK" in st.rxCmd :
            return True

    elif st.rxCmdNr == 0x36 :  # fast mode on/off
        print("parse_answer %02x: st.rxCmd = %s"%(st.rxCmdNr,st.rxCmd))
        if "ACK" in st.rxCmd :
            return True

    elif st.rxCmdNr == 0x37 :  # get milliseconds
        print("parse_answer %02x: st.rxCmd = %s"%(st.rxCmdNr,st.rxCmd))
        l = get_command_list()
        print("l=",l)
        st.rxMillis = l[0]
        print("received milliseconds:",st.rxMillis)
        return True

    elif st.rxCmdNr == 0x38 :  # copy all parameters from EEPROM to RAM
        print("parse_answer %02x: st.rxCmd = %s"%(st.rxCmdNr,st.rxCmd))
        if "ACK" in st.rxCmd :
            return True

    elif st.rxCmdNr == 0x39 :  # write all parameters from RAM to EEPROM
        print("parse_answer %02x: st.rxCmd = %s"%(st.rxCmdNr,st.rxCmd))
        if "ACK" in st.rxCmd :
            return True

    elif st.rxCmdNr == 0x3A :  # RESET using watchdog - endless loop
        print("parse_answer %02x: st.rxCmd = %s"%(st.rxCmdNr,st.rxCmd))
        if "ACK" in st.rxCmd :
            return True

    elif st.rxCmdNr == 0x3B :  # clear eeprom  ??? plpl test eeprom if ram space is left
        print("parse_answer %02x: st.rxCmd = %s"%(st.rxCmdNr,st.rxCmd))
        if "ACK" in st.rxCmd :
            return True

    elif st.rxCmdNr == 0x3C :  # check if motor connected
        print("parse_answer %02x: st.rxCmd = %s"%(st.rxCmdNr,st.rxCmd))
        l = get_command_list()
        print("0x3C: l=",l)
        st.rxMotConn = int(l[0])
        print("received motor connected:",st.rxMotConn);
        return True





    elif st.rxCmdNr == 0x3D :  # open and close valve to store times
        print("parse_answer %02x: st.rxCmd = %s"%(st.rxCmdNr,st.rxCmd))
        if "ACK" in st.rxCmd :
            return True

    elif st.rxCmdNr == 0x3E :  # switch off current motor
        print("parse_answer %02x: st.rxCmd = %s"%(st.rxCmdNr,st.rxCmd))
        if "ACK" in st.rxCmd :
            return True

    elif st.rxCmdNr == 0x3F :  # read motor current
        print("parse_answer %02x: st.rxCmd = %s"%(st.rxCmdNr,st.rxCmd))
        l = get_command_list()
        print("l=",l)
        st.rxMotImA = float(l[0])
        print("received mA:",st.rxMotImA);
        return True

    elif st.rxCmdNr == 0x40 :  # LCD-light on/off
        print("parse_answer %02x: st.rxCmd = %s"%(st.rxCmdNr,st.rxCmd))
        if "ACK" in st.rxCmd :
            return True

    elif st.rxCmdNr == 0x41 :  # read jumper settings
        print("parse_answer %02x: st.rxCmd = %s"%(st.rxCmdNr,st.rxCmd))
        l = get_command_list()
        print("l=",l)
        st.jumpers = int(l[0], 16)
        print("jumper setting = %02x:"%(st.jumpers));
        return True




    return False # values not found while parsing
        







# ----------------
# ----- test -----
# ----------------

if __name__ == "__main__" :
    pass
    # usage example
