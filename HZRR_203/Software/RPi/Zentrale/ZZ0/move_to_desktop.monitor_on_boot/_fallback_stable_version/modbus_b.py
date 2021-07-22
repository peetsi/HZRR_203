#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import usb_ser_b as us
import threading as th

#from usb_ser import *
from hr2_variables import *


import vorlaut as vor

st = Status()


def checksum( s ) :
    # s   binary array like:  b'xxx'
    cs = 0
    for c in s :
        cs += ord(c)
    cs = cs & 0xFFFF    # make unsigned 16 bit
    return cs


def lrc_parity( s ) :
    # s   binary array like:  b'xxx'
    lrc = 0
    for c in s :
       lrc = lrc ^ ord(c)
    lrc = lrc & 0x00FF
    return lrc

def __callingThread():
    return th.currentThread().getName().upper()

def wrap_modbus( adr, fnc, contr, cmdstr ) :
    # generates complete command from input:
    # adr      module address
    # fnc      function number
    # contr    regulator number 1,2,3,4 or 0 for module
    # cmdstr   command string ; could be "" empty
    # return:  byte array
    cmd = "%02X%02X%1X%s%s"%(int(adr), int(fnc), int(contr), PROT_REV, str(cmdstr) )
    cs = checksum( cmd )
    cmd = "%s%04X"%(cmd,cs)
    lrc = lrc_parity( cmd )
    cmd = ":%s%02X\r\n"%(cmd, lrc)
    cmd.encode()     # make byte-array
    return cmd

def unwrap_modbus( line ) :
    '''
    a command string of the fillowing form has to be read
    example is the answer to a 'ping' command Nr. 02 to mdule adr.02
    // ":0002021b VM25.7 RM25.8 VE0.0 RE0.0 RS0.0 PM88 0A003F\r\n"
    // :     lead-in
    // 00    master-address of packet (central PC)
    // 02    command nr to which was answered
    // 02    from-address (own module address)
    // 1     sub-address, 0=module, 1,2,3 is regulator 0,1,2
    // b     protocol type b for HZRR200
    //    >>> payload string >>>
    // VM25.7 RM25.8 VE0.0 RE0.0 RS0.0 PM88
    // 0A00  checksum
    // 3F    LRC
    // \r\n  cr-lf at end of line
    '''
    # check leading ':' and compare checksum and LRC to be valid
    # line      binary array containing received line to be checked
    # return:   byte-array containing complete line without ':', cs, LRC
    calcLrc = 0
    calcCsm = 0
    lineLrc = 0
    lineCsm = 0

    err_rx = 0
    l = len( line )
    if l==0 :
        err_rx |= 1
        return False, "err: len=0"

    if line[0] != ":" :
        return False, "err: wrong lead-in"


    s0 = line[l-4:l-2]
    s0 = s0.upper()           # user only uppercase hex 'A'...'F'
    try:
        lineLrc = int(s0,base=16)
    except Exception as e:
        vor.vorlaut(3,e)
        err_rx |= 2
    else:
        calcLrc  = lrc_parity( line[ 1 : l-4 ] )
    s1 = line[l-8:l-4]
    s1 = s1.upper()           # use only uppercase hex 'A'...'F'
    try:
        lineCsm = int(s1,base=16)
    except Exception as e:
        vor.vorlaut( 3, e)
        err_rx |= 4
    else:
        calcCsm  = checksum( line[ 1 : l-8 ] )

    if lineLrc==calcLrc and lineCsm==calcCsm :
        return True, line[ 1 : l-8 ]
    else:
        return False, "err_rx=%04X"%(err_rx)
    #finally:
    #    us.ser_obj.unblock(1,ct=__callingThread())


def parse_modbus(cmd):
   #us.ser_obj.blockStatus(1,ct=__callingThread())
   #us.ser_obj.block(1,ct=__callingThread())
   #try:

    # the returned command starts from master-address and
    # ends including the payload string (omitting checksum and LRC

    if cmd[0:1] != "00":
        return False
    st.cmdNr     = int(cmd[3:4])
    st.adrSender = int(cmd[5:6])
    st.subAdr    = int(cmd[7])
    if st.subAdr not in [0,1,2,3]:
        return False
    if cmd[8] != PROT_REV:
        return False

    if st.cmdNr == 1:
        if "ACK" in cmd[8:] :
            return True
        else:
            return False
    
    if st.cmdNr == 2:
        if st.subAdr == 0:
            if "ACK" in cmd[8:] :
                return True
        elif st.subAdr in [1,2,3]:
            pass
            # read values
        else:
            return False
    #finally:
    #    us.ser_obj.unblock(1,ct=__callingThread())
            



# ----------------
# ----- test -----
# ----------------

if __name__ == "__main__" :
    # usage example
    modAdr = 2
    cmd    = 1    # ping-command
    madr   = 0    # address module (not reg. 1,2 or 3
    cmdtxt = ""   # no data needed
    txCmd = wrap_modbus( modAdr, cmd, 0, cmdtxt )
    print("modbus-string=",txCmd)

    # ATTENTION: make a STRING out of the binary array !!!
    #ds = txCmd.decode()
    
    s = unwrap_modbus( txCmd )
    print("unwrapped    =",s)
    
    # test special commands
    tempSend = 45.6
    txCmd = wrap_modbus( modAdr, 0x20, 0, ' '+str(tempSend)+' ' )
    print(txCmd)
    
