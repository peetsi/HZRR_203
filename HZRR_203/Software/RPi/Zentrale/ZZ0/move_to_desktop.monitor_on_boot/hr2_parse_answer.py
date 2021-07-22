#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hr2_variables import *
import threading as th
import hz_rr_debug as dbg

dbg = dbg.Debug(1)

class Buffer_answer():

    def __init__(self):
        self.__from_terminal=False
        self.__ser_grab = ""

    def get(self):
        x = self.__ser_grab
        #+x2= dbg.__ser_grab
        #+x = x[1:] + "\n\n[CONSOLE LOG]\n" + x2[1:]
        self.__rst()
        #dbg.__rst()
        return x[1:]

    def __rst(self):
        self.__ser_grab = ""
        self.from_term(False)

    def add(self, x):
        if self.__from_terminal == True:
            self.__ser_grab += "\n" + x
            #dbg.from_term(True)
            #dbg.add(x)

    def from_term(self, v=True):
        if v != False:
            self.__from_terminal = True
        else:
            self.__from_terminal = False



pa_to_ser_obj = Buffer_answer()


def get_command_list():
    global pa_to_ser_obj

    ''' split ',' separated values from st.rxCmd in list '''
    if (st.rxCmd == ""):
        return 1
    pa_to_ser_obj.add('st.rxCmd: %s'%(str(st.rxCmd)))
    l = st.rxCmd.split(",")

    while l[0] == '' :
        l.pop(0)
    while l[-1] == '' :
        l.pop()
    return l

def __callingThread():
    return th.currentThread().getName().upper()

def parse_string():
    using_rxCmd = st.mon_rx_cpy
    dbg.m("using_rxCmd:",using_rxCmd, "/ string in st.rxCmd:",st.rxCmd,cdb=2)
    if ((using_rxCmd=="") or (len(using_rxCmd) < 9)):
        dbg.m("received data trash. string too small:",using_rxCmd,cdb=2)
        return False # string too small
    try:
        st.rxAdr    = int(using_rxCmd[0:2],16)
        st.rxCmdNr  = int(using_rxCmd[2:4],16)
        st.rxSender = int(using_rxCmd[4:6],16)
        st.rxSubAdr = int(using_rxCmd[6:7])
        st.rxProt   = using_rxCmd[7:8]
        rx_return_val = ('rxAdr:',st.rxAdr,'rxCmdNr:',st.rxCmdNr, \
                        'rxSender:',st.rxSender, 'rxProt:',st.rxProt)
    except ValueError as e:
        dbg.m("value_error:", e)
        return False
    except Exception as e:
        dbg.m("error:", e)
        return False
    pa_to_ser_obj.add('parse_string: %s'%(str(rx_return_val)))
    st.rxCmd = using_rxCmd[9:-7] # remove address header and checksum trailer
    modAdr = st.rxSender
    if st.rxProt != PROT_REV:
        return True # test

    elif st.rxCmdNr == 1 :  # ping command
        if "ACK" in st.rxCmd :
            pa_to_ser_obj.add('PING:ACK')
            return True

    elif st.rxCmdNr == 2 :  # read status values part 1
        if st.rxSubAdr == 0 :
            if "ACK" in st.rxCmd :   # "ACK" - no data to be sent
                pa_to_ser_obj.add('READ_STAT(cn2):ACK  -- (rxSubAdr == 0)')
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
                    cn2_mon["SN"] = v
                    #print(cn2)
                else:
                    nm = v[0:2]
                    try:
                        cn2_mon[nm]=float(v[2:])
                    except ValueError as e:
                        dbg.m("parser_answer() value_error:", e)
                        pass
                    except Exception as e:
                        dbg.m("parse_answer() error:", e)
                        pass
            #print(cn2)
            pa_to_ser_obj.add('READ_STAT->CN2: %s'%(str(cn2)))
            return True

    # command 3 not implemented in rev hr2 (was in hr010)
    # sends regulator parameter -> new command
    elif st.rxCmdNr == 4 :  # read status values part 2
        if st.rxSubAdr == 0 :
            # "ACK" - no data received
            if "ACK" in st.rxCmd :
                pa_to_ser_obj.add('READ_STAT(cn4):ACK  -- (rxSubAdr == 0)')
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
                    cn4_mon[nm] = int(v[2:],16)
                else:           # other values can be handled as float
                    cn4_mon[nm] = float(v[2:])
                    if (v == "tMotTotal") or (v == "nMotLimit"):
                        # store additionaly in parameters
                        parameters[modAdr-1]['r'][st.rxSubAdr-1][v] = float(v[2:])
            pa_to_ser_obj.add('READ_STAT->CN4: %s'%(str(cn4)))
            pa_to_ser_obj.add('READ_STAT->PARAMETER: %s'%(str(parameter)))
            set_cn('s')
            return True



def parse_answer():
    # ":0002021b VM25.7 RM25.8 VE0.0 RE0.0 RS0.0 PM88 0A003F"
    # where:
    # st.rxCmd = "0002021b VM25.7 RM25.8 VE0.0 RE0.0 RS0.0 PM88";
    # csum="0A00"; lrc="3F"
    using_rxCmd = st.rxCmd
    st.mon_rx_cpy = using_rxCmd
    dbg.m("using_rxCmd:",using_rxCmd, "/ string in st.rxCmd:",st.rxCmd,cdb=2)
    if ((using_rxCmd=="") or (len(using_rxCmd) < 9)):
        dbg.m("received data trash. string too small:",using_rxCmd,cdb=2)
        return False # string too small
    try:
        st.rxAdr    = int(using_rxCmd[0:2],16)
        st.rxCmdNr  = int(using_rxCmd[2:4],16)
        st.rxSender = int(using_rxCmd[4:6],16)
        st.rxSubAdr = int(using_rxCmd[6:7])
        st.rxProt   = using_rxCmd[7:8]
        rx_return_val = ('rxAdr:',st.rxAdr,'rxCmdNr:',st.rxCmdNr, \
                        'rxSender:',st.rxSender, 'rxProt:',st.rxProt)
    except ValueError as e:
        dbg.m("value_error:", e)
        return False
    except Exception as e:
        dbg.m("error:", e)
        return False

    pa_to_ser_obj.add('parse_answer: %s'%(str(rx_return_val)))

    st.rxCmd = using_rxCmd[9:-7] # remove address header and checksum trailer

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
        return True # test

    elif st.rxCmdNr == 1 :  # ping command
        if "ACK" in st.rxCmd :
            pa_to_ser_obj.add('PING:ACK')
            return True

    elif st.rxCmdNr == 2 :  # read status values part 1
        if st.rxSubAdr == 0 :
            if "ACK" in st.rxCmd :   # "ACK" - no data to be sent
                pa_to_ser_obj.add('READ_STAT(cn2):ACK  -- (rxSubAdr == 0)')
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
                    nm = v[0:2]
                    try:
                        cn2[nm]=float(v[2:])
                    except ValueError as e:
                        dbg.m("parser_answer() value_error:", e)
                        pass
                    except Exception as e:
                        dbg.m("parse_answer() error:", e)
                        pass
            #print(cn2)
            pa_to_ser_obj.add('READ_STAT->CN2: %s'%(str(cn2)))
            return True

    # command 3 not implemented in rev hr2 (was in hr010)
    # sends regulator parameter -> new command
    elif st.rxCmdNr == 4 :  # read status values part 2
        if st.rxSubAdr == 0 :
            # "ACK" - no data received
            if "ACK" in st.rxCmd :
                pa_to_ser_obj.add('READ_STAT(cn4):ACK  -- (rxSubAdr == 0)')
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
                    cn4[nm] = float(v[2:])
                    if (v == "tMotTotal") or (v == "nMotLimit"):
                        # store additionaly in parameters
                        parameters[modAdr-1]['r'][st.rxSubAdr-1][v] = float(v[2:])
            pa_to_ser_obj.add('READ_STAT->CN4: %s'%(str(cn4)))
            pa_to_ser_obj.add('READ_STAT->PARAMETER: %s'%(str(parameter)))
            set_cn('s')
            return True

    elif st.rxCmdNr == 5:  # read parameter: module / reg.part 1
        #timer1Tic,tMeas,dtBackLight,tv0,tv1,tr0,tr1,
        #tVlRxValid,tempZiSoll,tempTolRoom
        l = get_command_list()
        par = parameters[modAdr-1]
        if st.rxSubAdr == 0:
            # read timer1Tic,tMeas,dtBackLight,
            #   tv0,tv1,tr0,tr1,tVlRxValid,tempZiSoll,tempZiToly
            for n in par:
                if n == "r":
                    break # last value terminated in dict
                par[n]=float(l.pop(0))
            pa_to_ser_obj.add('READ_PARAM->par = parameters[modAdr-1]: %s'%(str(par)))
            return True

        elif st.rxSubAdr in [1,2,3]:
            # read:
            #   active, motIMin, motIMax, tMotDelay, tMotMin, tMotMax,
            #   dtOpen, dtClose, dtOffset
            pr = par["r"][st.rxSubAdr-1]
            start=False
            for n in pr:          # start at begin of directory
                pr[n]=float(l.pop(0))
                if l == []:     # last item provided
                    break
            pa_to_ser_obj.add('READ_PARAM->pr = par["r"][st.rxSubAdr-1]: %s'%(str(pr)))
            return True

    elif st.rxCmdNr == 6:  # read parameter: module / reg.part 2
        dbg.m("parse_answer %02x: st.rxCmd = %s"%(st.rxCmdNr,st.rxCmd))
        if st.rxSubAdr == 0:
            # "ACK" - no data available
            if "ACK" in st.rxCmd :
                pa_to_ser_obj.add('READ_PARAM-ACK (st.rxSubAdr == 0)')
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
                    pr[n]=float(l.pop(0))
                    if l == []:     # last item provided
                        break
            pa_to_ser_obj.add('READ_PARAM->pr = par["r"][st.rxSubAdr-1]: %s'%(str(pr)))
            return True
            #pr = parameters[modAdr-1]["r"][st.rxSubAdr-1][n] = number


    elif st.rxCmdNr == 7:  # read parameter: module / reg.part 3
        dbg.m("parse_answer %02x: st.rxCmd = %s"%(st.rxCmdNr,st.rxCmd))
        if st.rxSubAdr == 0:
            # "ACK" - no data available
            if "ACK" in st.rxCmd :
                pa_to_ser_obj.add('READ_PARAM-ACK (st.rxSubAdr == 0)')
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
                    pr[n]=float(l.pop(0))
                    if l == []:     # last item provided
                        break
            #parameter = parameters[modAdr-1]
            pa_to_ser_obj.add('READ_PARAM->pr = par["r"][st.rxSubAdr-1]: %s'%(str(pr)))
            return True


    elif st.rxCmdNr == 0x20 :  # Zentrale Vorlauftemperatur received
        dbg.m("parse_answer %02x: st.rxCmd = %s"%(st.rxCmdNr,st.rxCmd))
        if "ACK" in st.rxCmd :
            pa_to_ser_obj.add('zentrale_vorlauftemp->ACK: %s,%s'%(str(st.rxCmdNr),str(st.rxCmd)))
            return True


    elif st.rxCmdNr == 0x22 :  # setze parameter
        dbg.m("parse_answer %02x: st.rxCmd = %s"%(st.rxCmdNr,st.rxCmd))
        if "ACK" in st.rxCmd :
            pa_to_ser_obj.add('set_param(0x22)->ACK: %s,%s'%(str(st.rxCmdNr),str(st.rxCmd)))
            return True

    elif st.rxCmdNr == 0x23 :  # setze parameter
        dbg.m("parse_answer %02x: st.rxCmd = %s"%(st.rxCmdNr,st.rxCmd))
        if "ACK" in st.rxCmd :
            pa_to_ser_obj.add('set_param(0x23)->ACK: %s,%s'%(str(st.rxCmdNr),str(st.rxCmd)))
            return True


    elif st.rxCmdNr == 0x24 :  # setze parameter
        dbg.m("parse_answer %02x: st.rxCmd = %s"%(st.rxCmdNr,st.rxCmd))
        if "ACK" in st.rxCmd :
            pa_to_ser_obj.add('set_param(0x24)->ACK: %s,%s'%(str(st.rxCmdNr),str(st.rxCmd)))
            return True

    elif st.rxCmdNr == 0x25 :  # set special parameters
        dbg.m("parse_answer %02x: st.rxCmd = %s"%(st.rxCmdNr,st.rxCmd))
        if "ACK" in st.rxCmd :
            pa_to_ser_obj.add('set_special_param->ACK: %s,%s'%(str(st.rxCmdNr),str(st.rxCmd)))
            return True

    elif st.rxCmdNr == 0x30 :  # reset all parameters to factory settings
        dbg.m("parse_answer %02x: st.rxCmd = %s"%(st.rxCmdNr,st.rxCmd))
        if "ACK" in st.rxCmd :
            pa_to_ser_obj.add('factory_reset->ACK: %s,%s'%(str(st.rxCmdNr),str(st.rxCmd)))
            return True

    elif st.rxCmdNr == 0x31 :  # move valve; time and direction
        dbg.m("parse_answer %02x: st.rxCmd = %s"%(st.rxCmdNr,st.rxCmd))
        if "ACK" in st.rxCmd :
            pa_to_ser_obj.add('move_valve->ACK: %s,%s'%(str(st.rxCmdNr),str(st.rxCmd)))
            return True

    elif st.rxCmdNr == 0x34 :  # set normal operation
        dbg.m("parse_answer %02x: st.rxCmd = %s"%(st.rxCmdNr,st.rxCmd))
        if "ACK" in st.rxCmd :
            pa_to_ser_obj.add('set_normal_operation->ACK: %s,%s'%(str(st.rxCmdNr),str(st.rxCmd)))
            return True

    elif st.rxCmdNr == 0x35 :  # set regulator active/inactive
        dbg.m("parse_answer %02x: st.rxCmd = %s"%(st.rxCmdNr,st.rxCmd))
        if "ACK" in st.rxCmd :
            pa_to_ser_obj.add('reg_set->ACK: %s,%s'%(str(st.rxCmdNr),str(st.rxCmd)))
            return True

    elif st.rxCmdNr == 0x36 :  # fast mode on/off
        dbg.m("parse_answer %02x: st.rxCmd = %s"%(st.rxCmdNr,st.rxCmd))
        if "ACK" in st.rxCmd :
            pa_to_ser_obj.add('fast_mode->ACK: %s,%s'%(str(st.rxCmdNr),str(st.rxCmd)))
            return True

    elif st.rxCmdNr == 0x37 :  # get milliseconds
        l = get_command_list()
        st.rxMillis = l[0]
        dbg.m("COMMAND= %02x: st.rxCmd= %s"%(st.rxCmdNr,st.rxCmd),"/ l=",str(l),"/ recv milliseconds:",st.rxMillis)
        pa_to_ser_obj.add('get_millis->ACK: %s,%s,%s'%(str(st.rxCmdNr),str(st.rxCmd),str(st.rxMillis)))
        return True

    elif st.rxCmdNr == 0x38 :  # copy all parameters from EEPROM to RAM
        dbg.m("parse_answer %02x: st.rxCmd = %s"%(st.rxCmdNr,st.rxCmd))
        if "ACK" in st.rxCmd :
            pa_to_ser_obj.add('cpy_eep2ram->ACK: %s,%s'%(str(st.rxCmdNr),str(st.rxCmd)))
            return True

    elif st.rxCmdNr == 0x39 :  # write all parameters from RAM to EEPROM
        dbg.m("parse_answer %02x: st.rxCmd = %s"%(st.rxCmdNr,st.rxCmd))
        if "ACK" in st.rxCmd :
            pa_to_ser_obj.add('cpy_ram2eep->ACK: %s,%s'%(str(st.rxCmdNr),str(st.rxCmd)))
            return True

    elif st.rxCmdNr == 0x3A :  # RESET using watchdog - endless loop
        dbg.m("parse_answer %02x: st.rxCmd = %s"%(st.rxCmdNr,st.rxCmd))
        if "ACK" in st.rxCmd :
            pa_to_ser_obj.add('watchdog_reset->ACK: %s,%s'%(str(st.rxCmdNr),str(st.rxCmd)))
            return True

    elif st.rxCmdNr == 0x3B :  # clear eeprom  ??? plpl test eeprom if ram space is left
        dbg.m("parse_answer %02x: st.rxCmd = %s"%(st.rxCmdNr,st.rxCmd))
        if "ACK" in st.rxCmd :
            pa_to_ser_obj.add('clear_eep->ACK: %s,%s'%(str(st.rxCmdNr),str(st.rxCmd)))
            return True

    elif st.rxCmdNr == 0x3C :  # check if motor connected
        dbg.m("parse_answer %02x: st.rxCmd = %s"%(st.rxCmdNr,st.rxCmd))
        l = get_command_list()
        dbg.m("0x3C: l=",l)
        st.rxMotConn = int(l[0])
        dbg.m("received motor connected:",st.rxMotConn)
        pa_to_ser_obj.add('motor_connected->ACK: mot_connected:%s (%s,%s)'%(str(st.rxMotConn),str(st.rxCmdNr),str(st.rxCmd)))
        return True

    elif st.rxCmdNr == 0x3D :  # open and close valve to store times
        dbg.m("parse_answer %02x: st.rxCmd = %s"%(st.rxCmdNr,st.rxCmd))
        if "ACK" in st.rxCmd :
            pa_to_ser_obj.add('open_close_valve->ACK: %s,%s'%(str(st.rxCmdNr),str(st.rxCmd)))
            return True

    elif st.rxCmdNr == 0x3E :  # switch off current motor
        dbg.m("parse_answer %02x: st.rxCmd = %s"%(st.rxCmdNr,st.rxCmd))
        if "ACK" in st.rxCmd :
            pa_to_ser_obj.add('mot_off->ACK: %s,%s'%(str(st.rxCmdNr),str(st.rxCmd)))
            return True

    elif st.rxCmdNr == 0x3F :  # read motor current
        l = get_command_list()
        st.rxMotImA = float(l[0])
        dbg.m("parse_answer %02x: st.rxCmd = %s"%(st.rxCmdNr,st.rxCmd),"// l=",l,"// received mA:",st.rxMotImA)
        pa_to_ser_obj.add('mot_current->ACK: %s (%s,%s)'%(str(st.rxMotImA),str(st.rxCmdNr),str(st.rxCmd)))
        return True

    elif st.rxCmdNr == 0x40 :  # LCD-light on/off
        dbg.m("parse_answer %02x: st.rxCmd = %s"%(st.rxCmdNr,st.rxCmd))
        if "ACK" in st.rxCmd :
            pa_to_ser_obj.add('lcd_backlight->ACK: %s,%s'%(str(st.rxCmdNr),str(st.rxCmd)))
            return True

    elif st.rxCmdNr == 0x41 :  # read jumper settings
        l = get_command_list()
        st.jumpers = int(l[0], 16)
        dbg.m("parse_answer %02x: st.rxCmd = %s"%(st.rxCmdNr,st.rxCmd),"// jumper setting = %02x:"%(st.jumpers))
        pa_to_ser_obj.add('get_jumpers->ACK: %s (%s,%s)'%(str(st.jumpers),str(st.rxCmdNr),str(st.rxCmd)))
        return True

    pa_to_ser_obj.add('Error: (%s,%s)'%(str(st.rxCmdNr),str(st.rxCmd)))
    return False # values not found while parsing



#pa_to_ser_obj

# ----------------
# ----- test -----
# ----------------

if __name__ == "__main__" :
    print("buffer object test")
    pa_to_ser_obj.from_term()
    pa_to_ser_obj.add('test')
    print("get:",pa_to_ser_obj.get())
    pass
    # usage example
