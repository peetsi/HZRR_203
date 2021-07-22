                                                                                                                    #!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
hr2_netstatus
-------------
- send and receive commands permanently and make statistics
  to find networking problems
- use stand-alone communication to evaluate bus-related problems
statistics: 
- ping selected modules, wait for answer, evaluate
  - response time
  - response from address - could differ from requested address
  - answer ACK/NAK or timeout
  perform all functions directely and independently from existing 
  softwae modules to avoid interference with other timings/errors
'''

import time
import os
import serial
import ast
import glob
import numpy as np
import matplotlib.pyplot as plt

#import hr2_parse_answer as pan
import modbus_b as mb
#import vorlaut as vor
import usb_ser_b as us
#from usb_ser_b import ser_add_work

from hr2_variables import *
import copy
#import hz_rr_debug as dbg
#import heizkreis_config as hkr_cfg
import hz_rr_config as cg
hkr_cfg = cg.hkr_obj

# *****************************
# global variables

# settings
testMotors  = [(1,1),(1,3)]

# internal use
motCurrent = 0
hostname = ""
tempPath = "temp/"
filename = ""
motTestFilename = None

# *** parameter names
#  0   1  2    3    4    5    6  7    8   9 + "r"
# 10,120,10,40.0,75.0,32.0,46.0,30,20.0,0.5,
parModNames=[
    "timer1Tic","tMeas","dtBackLight",\
    "tv0","tv1","tr0","tr1","tVlRxValid",\
    "tempZiSoll","tempZiTol","r"
]

parRegNames=[\
    # c5: 0 1  2  3   4  5  6  7    8   9
    #     1,5,70,80,100,40,28,34,3000,500,
    [ "active","motIMin","motIMax","tMotDelay",\
        "tMotMin","tMotMax","dtOpen","dtClose",\
        "dtOffset","dtOpenBit"],\
    # c6:   10    11    12   13   14   15
    #    0.100,0.000,0.000,1.00,1.00,1.00,
    [ "pFakt","iFakt","dFakt","tauTempVl","tauTempRl","tauM"],\
    # c7:    16      17  18  19   20   21    22
    #    50.000,-50.000,600,900,2000,2000,2.000,
    [ "m2hi","m2lo","tMotPause","tMotBoost","dtMotBoost",\
    "dtMotBoostBack","tempTol"]\
    #"tMotTotal","nMotLimit" are sent with status2 - cmd 4
]



# *** error flag definition
RXE_SHORT     = 0x0001  # received string is too short
RXE_VALUE     = 0x0002  # wrong value
RXE_HEADER    = 0x0004  # wrong header format
RXE_ADR       = 0x0008  # wrong/not matching answer address
RXE_CMD       = 0x0010  # wrong/not matching command
RXE_MOD       = 0x0020  # wrong/not matching module number
RXE_REG       = 0x0040  # wrong/not matching regulator
RXE_PROT      = 0x0080  # unknown protocol version
RXE_CHECK     = 0x0100  # wrong checksum or RLL
RXE_NAK       = 0x0200  # no acknkwledge
RXE_TX_TOUT   = 0x0400  # timeout sending command
RXE_TX_SEREX  = 0x0800  # serial Tx exception
RXE_TX_EXCEPT = 0x0800  # generat serial Tx exception
RXE_RX_TOUT   = 0x1000  # timeout receiving command
RXE_RX_SEREX  = 0x2000  # serial Tx exception
RXE_RX_EXCEPT = 0x2000  # generat serial Tx exception
RXE_RX_CODE   = 0x4000  # encode-decode error in string




def get_modules():
    antwort = hkr_cfg.get_heizkreis_config(0,1)
    return( antwort[1] )

def all_mod_regs(mods,regs):
    ''' return list with all modules (m,0) or all regs (m,1)..(m,3)
        from regs input list e.g. [0,1,2,3] '''
    # regs = [0,1,2,3] or part of it
    lAll=[]
    for mod in mods:
        for r in regs:
            lAll.append( (mod,r) )
    print(lAll)
    return lAll


# **************************************
# Serial Port settings
#

serTimeout = 0.5
serialPort_PIthree = "/dev/serial/by-path/platform-3f980000.usb-usb-0:1.1.3:1.0-port0"
serialPort_PIfour  = "/dev/serial/by-path/platform-fd500000.pcie-pci-0000:01:00.0-usb-0:1.4:1.0-port0"
# select serial port depending on installed Raspberry Pi:
serPort = serialPort_PIfour
br = 115200

def ser_instant() :
    ser = None
    err=0
    try:
        ser = serial.Serial(
            port        = serPort,
            baudrate    = br,
            parity      = serial.PARITY_NONE,
            stopbits    = serial.STOPBITS_TWO,
            bytesize    = serial.EIGHTBITS,
            timeout     = serTimeout,
            write_timeout=serTimeout
            )
    except serial.SerialException as e:
        print( 3,  "01 cannot find: %s"%(serPort))
        print( 3,  "   exception = %s"%(e))
        err = 1
    except Exception as e:
        print( 3,  "02 something else is wrong with serial port: %s"%(serPort))
        print( 3,  "   exception = %s"%(e))
        err = 2
    return err, ser


def ser_open(ser):
    err=0
    try:
        ser.open() # open USB->RS485 connection
    except serial.SerialException as e:
        print( 3,  "03 cannot open: %s"%(serPort))
        print( 3,  "   exception = %s"%(e))
        err = 3
    except  Exception as e:
        print( 3,  "04 something else is wrong with serial port:"%(serPort))
        print( 3,  "   exception = %s"%(e))
        err = 4
    return err


def ser_check():
    err = 0
    err,ser = ser_instant()
    if (err==0):
        if (ser.isOpen() == False) :
            err = ser_open(ser)
            if( err ) :
                print("rs485 Netz nicht verbunden: %d"%(err))
                return err,ser
            else:
                print("rs485 Netz geoeffnet")
            time.sleep(0.1)
        print("rs485 Netz verbunden")
    return err, ser




def txrx_Command_2( txCmd ):
    err=0
    rxDatB = None
    rxDat  = None
    # NOTE wait some time to make sure the bus is released
    #      by other modules
    #      on zz0 with 2 modules 0.1s still lead to errors
    #      0.13 sec seemed to perform well
    time.sleep(0.13)  # 0.1 makes timeout errors zz0
    if type(txCmd)==str :
        txCmd = txCmd.encode()  # byte-array needed for serial comm.
    ser.reset_input_buffer()
    #ser.reset_output_buffer()
    #print("send command:",txCmd)
    try:
        ser.write(txCmd)       # send command
    except serial.SerialTimeoutException as e:  # only for tx timout !!!
        err |= RXE_TX_TOUT
        print(e)
        return err, rxDat
    except serial.SerialException as e:
        err |= RXE_TX_SEREX
        print(e)
        return err, rxDat
    except Exception as e:
        err |= RXE_TX_EXCEPT
        print(e)
        return err, rxDat
    # ??? not needed? ser.flush()  # send out tx-buffer 
    ser.flush()
    #while ser.out_waiting : # block until whole command is sent
    #    pass

    #time.sleep(0.05)
    tbeg = time.time()
    try:
        rxDatB = ser.readline()
    except serial.SerialException as e:
        err |= RXE_RX_SEREX
        print(e)
    except Exception as e:
        err |= RXE_RX_EXCEPT
        print(e)
    tend = time.time()
    to = ser.get_settings()["timeout"]
    if (tend-tbeg) > to:  # timeout occurred
        err |= RXE_RX_TOUT
        print("RX timeout")

    if rxDatB != None:
        try:
            rxDat = rxDatB.decode()
        except UnicodeDecodeError as e:
            rxDat = ""
            print(e)
            err |= RXE_RX_CODE
        except Exception as e:
            rxDat = ""
            print(e)
            err |= RXE_RX_CODE
    return err,rxDat



def comm_check( txDat, rxDat, rxErr):
    ''' compare sent and received command, use received error '''
    (txMod,txReg,txCmdNr) = txDat
    global motCurrent

    # module-regulator-commandNr for answer
    mrc = ["m%02dr%dc%d:"%(txMod,txReg,txCmdNr)]

    if rxErr:
        return rxErr,mrc

    # *** analyze answer string
    # checksum and modbus LLR:
    # analyze length
    if ((rxDat=="") or (len(rxDat) < 9)):
        print("rx string too small; rxDat= <",rxDat,">",end="")
        rxErr |= RXE_SHORT
        return rxErr,mrc
    else:
        # analyze checksums
        checksum, rxStr = mb.unwrap_modbus( rxDat )
        if not checksum :
            rxErr |= RXE_CHECK
            return rxErr,mrc
        # analyze header
        try:
            rxAdr    = int(rxStr[0:2],16)
            rxCmdNr  = int(rxStr[2:4],16)
            rxMod    = int(rxStr[4:6],16)
            rxReg    = int(rxStr[6:7])
            rxProt   = rxStr[7:8]
        except ValueError as e:
            print("value_error:", e)
            rxErr |= RXE_VALUE
            return rxErr,mrc
        except Exception as e:
            print("error:", e)
            rxErr |= RXE_HEADER
            return rxErr,mrc
        else:
            # compare header values
            if rxAdr != 0:
                rxErr |= RXE_ADR
            if rxMod != txMod:
                rxErr |= RXE_MOD
            if rxReg != txReg:
                rxErr |= RXE_REG
            if rxCmdNr != txCmdNr:
                rxErr |= RXE_CMD
            if rxProt != "b":
                rxErr |= RXE_PROT
        # check answer
        if txCmdNr in [1,0x20]:  # ping
            if not ("ACK" in rxStr) :  # in case of ping-command
                rxErr |= RXE_NAK

        if txCmdNr in [2,4]:
            # no ruther checks for data content
            pass 
        
        if txCmdNr in [5,6,7]:
            # save to parameter file
            print(rxStr)
            #:0005010b,10,120,10,40.0,75.0,32.0,46.0,30,20.0,0.5,09BE76
            # rxStr=
            # head,    --->        data                     <---,
            # 0005010b,10,120,10,40.0,75.0,32.0,46.0,30,20.0,0.5,
            if not rxErr:
                # add returned data
                pos0 = rxStr.find(",")+1
                mrc.append(rxStr[pos0:])
        
        if txCmdNr in [0x3F]:  # motor current
            l0=rxStr.split(",")
            try:
                motCurrent = int(l0[1])
            except Exception as e:
                print(e)
                motCurrent = 999  # mark error
                rxErr |= RXE_RX_EXCEPT
            
        #print("rxErr=%04X"%(rxErr))
        return rxErr,mrc


cmdNames = { 1:"ping", 2:"status 1", 4:"status2", 
             5:"parameter 1", 6:"parameter 2", 7:"parameter 3", 
             0x20:"set VLtemp",0x37:"get msec tics",0x3A:"RESET via watchdog - wait!",0x41:"get jumper settings" }


def do_test( fo, d ):
    [modules, regs, txCmdNr, txStr, tests] = d
    result=[]
    mrcList = []
    tcyc=time.time()   # time for a whole cycle
    for test in range(tests):
        print(test,end=":")
        for txMod in modules:
            dtcyc=time.time()-tcyc
            tcyc = time.time()
            res=[]
            print("+",end="")
            print("%.3f "%(dtcyc),end="")
            for txReg in regs:
                txCmd = mb.wrap_modbus( txMod, txCmdNr, txReg, txStr )
                print("txCmd = %s"%(txCmd.strip()), end=" ")
                t0 = time.time()
                txrxErr,rxDat = txrx_Command_2( txCmd )
                print("rxDat = %s"%(rxDat.strip()),end=" ")
                t1 = time.time()
                #print("string received:", rxDat, end="  ")
                #print("delay:",t1-t0, end="  ")
                txDat = (txMod,txReg,txCmdNr)
                rxErr,mrc = comm_check(txDat,rxDat,txrxErr)
                #print("check result: %04X"%(rxErr))
                mrcList.append(mrc)
                fo.write("# txCmd=%s -- rxDat=%s\n"%(txCmd.strip(),rxDat.strip()))
                res.append([txMod,txReg,t0,t1,rxErr,dtcyc])
            result.append(res)
            fo.write(str(res)+"\n")
        print()
    return result,mrcList




def send_command( repeat, txCmd, mod, reg, msg ):
    while repeat:
        repeat -=1
        txrxErr,rxDat = txrx_Command_2( txCmd )
        if not txrxErr:
            return txrxErr,rxDat
    if repeat == 0:
        print("cannot %s form mod%d reg%d"%(msg,mod,reg))
        return 1,None


def compare_txrx_dat( rxDat0, rxDat1, bug):
    ''' check if data in rx datasets are equal,
        bug==0: normal,   bug==1: remove double value in rxDat1'''
    sc0 = rxDat0.strip().split(",")
    sc0.pop(0)  # remove header
    sc0.pop()   # remove trailer
    sc1 = [ float(x) for x in sc0 ]
    rd0 = rxDat1.strip().split(",")
    rd0.pop(0)
    rd0.pop()
    rd1 = [ float(x) for x in rd0 ]
    print()
    print(sc1)
    print(rd1)
    # compare to verify
    if bug==1:
        sc1.pop(-3)  #NOTE remove added value due to bug in Modules
    for i in range(len(sc1)):
        if sc1[i] != rd1[i]:
            print("Verify FAILED")
            return 1
    print("Verify OK")
    return 0


def change_parameter( mod, reg, cmd, parname ):
    ''' - get a received parameter string from module, regulator (0,1,2,3),
          command nr cmd and the received data string
        - fill the data in a structure with the variable names
        ---> user provided: change the desired parameter
        - send the changed parameters back to the module
        - read parameter back anch check if change was successful '''
    #TODO use parname

    if cmd==5:  # parameter set 1
        if reg==0:  # module related parameters
            # *** read modul parameter
            txMod = mod
            txCmd = mb.wrap_modbus( txMod, cmd, reg, "" )
            txrxErr,rxDat = send_command( 5, txCmd,mod,reg,"read mod-par" )
            if txrxErr:
                return 1

            # *** fill read data in structure
            names = parModNames.copy()
            names.pop()  # remove last item "r" which has no direct value
            vals  = rxDat.split(",")
            vals.pop(0)  # remove left element with header
            parMod={}
            for i in range(len(names)):
                parMod[names[i]] = vals[i]
            print("parMod=",parMod    )
            
            # ***************************
            # *** change module parameter
            # ***************************
            #NOTE tbd by user, e.g.
            parMod["tr0"] = 41.0
            # ***************************

            # *** write back parameter to module
            txStr = ","  # tata string for transmission
            for par in names:
                hs = str( parMod[par] )
                if par == "tVlRxValid":
                    # Bug in module-software: send this value double
                    txStr += hs+","
                txStr += hs+","
            txCmd = mb.wrap_modbus( mod, 0x22, reg, txStr )
            txCmdSent = txCmd
            print("txCmd = %s"%(txCmd.strip()), end=" ")
            txrxErr,rxDat = send_command( 5, txCmd,mod,reg, "send mod-par " )
            if txrxErr:
                return 2
 
            # *** read back parameter to verify changes
            txCmd = mb.wrap_modbus( txMod, cmd, reg, "" )
            txrxErr,rxDat = send_command( 5, txCmd,mod,reg, "re-read mod-par " )
            if txrxErr:
                return 3

            # *** compare back-read data with sent data - verify
            rv = compare_txrx_dat( txCmdSent, rxDat, 1 )
            if rv :
                return 4


        elif reg in [1,2,3]:  # regulator related parameters
            # *** read regulator parameter set 1
            txMod = mod
            txCmd = mb.wrap_modbus( txMod, cmd, reg, "" )
            txrxErr,rxDat = send_command( 5, txCmd,mod,reg, "read reg-par1" )
            if txrxErr:
                return 1

            # *** fill read data in structure
            names = parRegNames[0].copy()
            vals  = rxDat.split(",")
            vals.pop(0)  # remove left element with header
            pars={}
            for i in range(len(names)):
                pars[names[i]] = vals[i]
            print("reg pars1=",pars )
            
            # ***************************
            # *** change module parameter
            # ***************************
            #NOTE tbd by user, e.g.
            pars["motIMax"] = 73   # set maximum motor current
            # ***************************

            # *** write back parameter to module
            txStr = ","  # tata string for transmission
            for par in names:
                hs = str( pars[par] )
                txStr += hs+","
            txCmd = mb.wrap_modbus( mod, 0x22, reg, txStr )
            txCmdSent = txCmd
            print("txCmd = %s"%(txCmd.strip()), end=" ")
            txrxErr,rxDat = send_command( 5, txCmd,mod,reg, "send reg-par1 " )
            if txrxErr:
                return 2
 
            # *** read back parameter to verify changes
            txCmd = mb.wrap_modbus( txMod, cmd, reg, "" )
            txrxErr,rxDat = send_command( 5, txCmd,mod,reg, "re-read reg-par1 " )
            if txrxErr:
                return 3

            # *** compare back-read data with sent data - verify
            rv = compare_txrx_dat( txCmdSent, rxDat, 0 )
            if rv :
                return 4


    elif cmd==6 and reg in [1,2,3]:  # parameter set 2
        # *** read regulator parameter set 2
        txMod = mod
        txCmd = mb.wrap_modbus( txMod, cmd, reg, "" )
        txrxErr,rxDat = send_command( 5, txCmd,mod,reg, "read reg-par2" )
        if txrxErr:
            return 1

        # *** fill read data in structure
        names = parRegNames[1].copy()
        vals  = rxDat.split(",")
        vals.pop(0)  # remove left element with header
        pars={}
        for i in range(len(names)):
            pars[names[i]] = vals[i]
        print("reg pars2=",pars )
        
        # ***************************
        # *** change module parameter
        # ***************************
        #NOTE tbd by user, e.g.
        pars["pFakt"] = 0.025    # proportional factor
        # ***************************

        # *** write back parameter to module
        txStr = ","  # tata string for transmission
        for par in names:
            hs = str( pars[par] )
            txStr += hs+","
        txCmd = mb.wrap_modbus( mod, 0x23, reg, txStr )
        txCmdSent = txCmd
        print("txCmd = %s"%(txCmd.strip()), end=" ")
        txrxErr,rxDat = send_command( 5, txCmd, "send reg-par2 " )
        if txrxErr:
            return 2

        # *** read back parameter to verify changes
        txCmd = mb.wrap_modbus( txMod, cmd, reg, "" )
        txrxErr,rxDat = send_command( 5, txCmd,mod,reg, "re-read reg-par2 " )
        if txrxErr:
            return 3

        # *** compare back-read data with sent data - verify
        rv = compare_txrx_dat( txCmdSent, rxDat, 0 )
        if rv :
            return 4

    elif cmd==7 and reg in [1,2,3]:  # parameter set 3
         # *** read regulator parameter set 3
        txMod = mod
        txCmd = mb.wrap_modbus( txMod, cmd, reg, "" )
        txrxErr,rxDat = send_command( 5, txCmd,mod,reg, "read reg-par3" )
        if txrxErr:
            return 1

        # *** fill read data in structure
        names = parRegNames[2].copy()
        vals  = rxDat.split(",")
        vals.pop(0)  # remove left element with header
        pars={}
        for i in range(len(names)):
            pars[names[i]] = vals[i]
        print("reg pars3=",pars )
        
        # ***************************
        # *** change module parameter
        # ***************************
        #NOTE tbd by user, e.g.
        #pars["tMotPause"]      = 1    # uint16_t;  sec;  time to stop motor after m2hi
        #pars["tMotBoost"]      = 1    # uint16_t;  sec;  time to keep motor open after m2lo increase flow
        #pars["dtMotBoost"]     = 500  # uint16_t;  ms;   motor-on time to open motor-valve for boost
        #pars["dtMotBoostBack"] = 600  # uint16_t;  ms;   motor-on time to close motor-valve after boost 
        #pars["tempTol"]        = 2.0  # float;     K;    temperature tolerance allowed for Ruecklauf
        # ***************************

        # *** write back parameter to module
        txStr = ","  # tata string for transmission
        for par in names:
            hs = str( pars[par] )
            txStr += hs+","
        txCmd = mb.wrap_modbus( mod, 0x24, reg, txStr )
        txCmdSent = txCmd
        print("txCmd = %s"%(txCmd.strip()), end=" ")
        txrxErr,rxDat = send_command( 5, txCmd, "send reg-par3 " )
        if txrxErr:
            return 2

        # *** read back parameter to verify changes
        txCmd = mb.wrap_modbus( txMod, cmd, reg, "" )
        txrxErr,rxDat = send_command( 5, txCmd,mod,reg, "re-read reg-par3 " )
        if txrxErr:
            return 3

        # *** compare back-read data with sent data - verify
        rv = compare_txrx_dat( txCmdSent, rxDat, 0 )
        if rv :
            return 4


    return 0
    pass






def save_parameter( mrcTotal,fParsName):
    ''' fit read parameters to their variable names and save them to file '''
    mrcTotal.sort()
    pars={}  # fill in all modules
    par={}   # fill in parameters of a module with its regulators
    for mrc in mrcTotal:
        '''
        # examples for mrcs:
        ['m02r0c5:', '10,120,10,40.0,75.0,32.0,46.0,30,20.0,0.5,']
        ['m02r1c5:', '1,5,70,80,100,40,28,34,3000,500,']
        ['m02r1c6:', '0.100,0.000,0.000,1.00,1.00,1.00,']
        ['m02r1c7:', '50.000,-50.000,600,900,2000,2000,2.000,']
        ['m02r2c5:', '1,5,70,80,100,40,28,34,3000,500,']
        ['m02r2c6:', '0.100,0.000,0.000,1.00,1.00,1.00,']
        ['m02r2c7:', '50.000,-50.000,600,900,2000,2000,2.000,']
        ['m02r3c5:', '1,5,70,80,100,40,28,34,3000,500,']
        ['m02r3c6:', '0.100,0.000,0.000,1.00,1.00,1.00,']
        ['m02r3c7:', '50.000,-50.000,600,900,2000,2000,2.000,']
        '''
        #print(mrc)
        m=int(mrc[0][1:3])
        r=int(mrc[0][4:5])
        c=int(mrc[0][6:7])

        #print(m,r,c)
        if not (m in pars):
            # generate nested dictionary structure
            pars[m]={}
            pars[m][1]={}
            pars[m][2]={}
            pars[m][3]={}
        if r==0:
            names = parModNames
            vals  = mrc[1].split(",")
            for i in range(len(names)):
                par[names[i]] = vals[i]
                pass
            #par["r"]={}  # dict for regulator dicts
            pars[m].update(par)  # add parameters to all parameter dictionary
            pass
        if r in [1,2,3]:
            cmdIdx = c-5  # commands 5,6,7 -> index 0,1,2
            names = parRegNames[cmdIdx]
            vals  = mrc[1].split(",")
            parRegPart = {}
            for i in range(len(names)):
                parRegPart[names[i]] = vals[i]
            pars[m][r].update(parRegPart)
        test = 1
    fPars=open(fParsName,"w")
    fPars.write(str(pars))
    fPars.close()
    '''
    # *** write .ini file
    import configparser 
    config = configparser.ConfigParser()
    for modNr in pars:
        par = pars[modNr]
        for ns in par:
            if ns in [1,2,3]:
                reg = ns
                label="Mod%02dr%d"%(modNr,reg)
                v = par[ns]
                config[label] = v
            else:
                label="mod%02d"%(modNr)
                config[label][ns] = par[ns]
            
    fParsIniName=fParsName.rstrip(".dat") + ".ini"
    with open(fParsIniName,"w") as fParsIni:
        config.write(fParsIni)
        pass
    '''

    return pars








def get_motor_time():
    tmot=0
    motdir=0
    a=input("Motor-on time in msec->")
    if a!="":
        tmot=int(a)
        a=input("Direction 0/zu 1/auf ->")
        if a != "":
            motdir=int(a)
            a=input("regulators 1,2,3 ->")
            b="[%s]"%(a)
            regs = ast.literal_eval(b)
        else:
            tmot=0  # no motor movement

    return tmot, motdir, regs





def motor_test(mod,reg):
    '''test motor of module mod and regulator reg'''
    '''return list with measured values'''
    # *** first test: close/oopen valve and monitor current
    repeat = 5
    delay  = 0.1
    tMotOn= 1500
    values=[]  # (t,on,I)

    cmdList=[]  # no later performance
    for n in range(repeat):
        # test closing motor valve
        hs="--- Mod%02d Reg%d test %d: close"%(mod,reg,n)
        print(hs)
        fo.write(hs+"\n")
        txStr = ","+str(tMotOn)+",0,"  # close valve
        result,mrcList=do_test(fo,[[mod], [reg], 0x31, txStr, 1])
        values.append([time.time(),-1,0])
        motOn=True
        while motOn:
            # read motor current
            result,mrcList=do_test(fo,[[mod], [0], 0x3F, "", 1])
            values.append([time.time(),-1,motCurrent])
            hs = "close motCurrent=%3dmA"%(motCurrent)
            print(hs)
            fo.write(hs+"\n")
            time.sleep(delay)
            if motCurrent < 2:
                motOn = 0
        time.sleep(delay)
        # test opening motor valve
        regs=[reg]
        hs="--- Mod%02d Reg%d test %d: open"%(mod,reg,n)
        print(hs)
        fo.write(hs+"\n")
        txCmdNr = 0x31  # move motor
        txStr = ","+str(tMotOn)+",1,"  # open valve
        result,mrcList=do_test(fo,[[mod], [reg], 0x31, txStr, 1])
        values.append([time.time(),1,0])
        motOn=True
        while motOn:
            # read motor current
            result,mrcList=do_test(fo,[[mod], [0], 0x3F, "", 1])
            values.append([time.time(),1,motCurrent])
            hs = "open motCurrent=%3dmA"%(motCurrent)
            print(hs)
            fo.write(hs+"\n")
            time.sleep(delay)
            if motCurrent < 2:
                motOn = 0
        time.sleep(delay)
    mval = [mod,reg,values]
    return mval






















def save_mot_test(mval):
    global filename
    global motTestFilename
    motTestFilename=filename.rstrip(".dat")+"_MotTest.dat"
    with open(motTestFilename,"w") as fmo:
        fmo.write(str(mval))




def plot_mot_test(mval):
    global filename
    global motTestFilename
    testPath = filename[ 0 : 1 + filename.rfind("/")]
    posbeg = filename.rfind("_") + 1
    posend = filename.rfind(".dat")
    dattim = filename[posbeg:posend]
    '''
    # *** use stored data if preferred in place of mval
    mtFiles = glob.glob(testPath + "*_MotTest.dat")
    mtFiles.sort()
    cnt=0
    for fName in mtFiles:
        print(cnt,fName)
        cnt += 1
    a = input("which file? ->")
    ai = int(a)
    motTestFilename = mtFiles[ai]
    with open(motTestFilename,"r") as fin:
        l = fin.read()
    mval = ast.literal_eval(l)
    #print(mval)
    '''
    # *** plot resulting measured values
    diagrams=len(mval) 
    """ plot all hr2data in one diagram. """
    cm2i = 1.0/2.54  # factor cm to insh
    #a4FormatQ = (29.7*cm2i,21.0*cm2i)
    #a3FormatQ = (42.0*cm2i,29.7*cm2i)
    oFormat   = (28.0*cm2i,diagrams*5*cm2i)
    diagsHor = 2
    diagsVer = int(diagrams/diagsHor + 1)
    #fig,axs = plt.subplots(2,int(diagrams/2 + 0.6),figsize=oFormat)
    fig,axs = plt.subplots(diagsVer,diagsHor,figsize=oFormat)
    plt.tight_layout()
    dcnt=0
    for d in mval:
        mod = d[0]
        reg = d[1]
        val = d[2]
        vala = np.array(val)
        t0  = vala[0][0]
        t   = vala[:,0]-t0
        on  = vala[:,1]
        ma  = vala[:,2]
        
        global hostname
        titelDiagramm = "HR2_"+hostname+"_Motor-Test_Mod%02dReg%d_"%(mod,reg)+dattim
        titel = "HR2_"+hostname+"_"+dattim
        picName = titel +".png"

        xpos = (dcnt % 2)
        ypos = int(dcnt / 2)

        axs[ypos,xpos].set_title( titelDiagramm )
        axs[ypos,xpos].plot(t,on,linestyle="-", label="%d/%d on"%(mod,reg))
        axs[ypos,xpos].plot(t,ma,linestyle="-", label="%d/%d mA"%(mod,reg))

        axs[ypos,xpos].grid("true")
        axs[ypos,xpos].set_ylabel("mA")
        axs[ypos,xpos].legend(fontsize="x-small")
        axs[ypos,xpos].set_xlabel("sec")

        dcnt += 1
               
    outfile = testPath + picName
    plt.savefig(outfile)

    plt.show()
    plt.close()
 




def select_modules(smod,sreg,scmd):
    print(60*"=")
    print("accept preset values by pressing <ENTER>")
    print("modules; e.g. 1,2,5; 99->all modules; x->Ende ? %s "%(smod),end="")
    a = input()
    if a == "99":
        mods = modules
    elif a == "":
        #TODO regs = list of comma delimited string items
        pass
    else:
        print("break")
        return [],[],0

    print("regulators; e.g. 0,1,2,3 ;  9->1,3;   x->Ende ? %s "%(sreg),end="")
    if a == "9":
        regs = [1,3]
    elif a == "":
        #TODO regs = list of comma delimited string items
        pass
    else:
        print("break")
        return [],[],0

    print("command Nr.; x->Ende ? %s "%(scmd),end="")
    a = input()
    if a=="":
        cmd = int(scmd)
    elif a in implemented:
        cmd = int(a)
    else:
        print("break")
        return [],[],0

    return (mods,regs,cmd)











def perform(a,fo,modules,tests):
    ''' perform commands from menu'''
    result = None
    cmdList = []
    if a=="0":
        return result
        pass
    elif a=="1":
        txCmdNr = 1  # ping
        regs=[0]
        txStr=""
        cmdList.append((0,[modules, regs, txCmdNr, txStr, tests]))
        pass
    elif a=="2":
        txCmdNr = 2  # regulator status 1
        regs=[1,2,3]
        txStr=""
        cmdList.append((0,[modules, regs, txCmdNr, txStr, tests]))
        pass
    elif a=="4":
        txCmdNr = 4  # regulator status 2
        regs=[1,2,3]
        txStr=""
        cmdList.append((0,[modules, regs, txCmdNr, txStr, tests]))
        pass

    elif a=="5":
        txCmdNr = 5  # read parameter set 1
        regs=[0,1,2,3]
        txStr=""
        cmdList.append((0,[modules, regs, txCmdNr, txStr, tests]))
        pass
    elif a=="6":
        txCmdNr = 6  # read parameter set 1
        regs=[1,2,3]
        txStr=""
        cmdList.append((0,[modules, regs, txCmdNr, txStr, tests]))
        pass
    elif a=="7":
        txCmdNr = 7  # read parameter set 1
        regs=[1,2,3]
        txStr=""
        cmdList.append((0,[modules, regs, txCmdNr, txStr, tests]))
        pass

    elif a=="20":
        # command 0x20 is e.g. ":02200b,45.6,02634C" for address 2
        txCmdNr = 0x20  # seet VLtemperature
        regs=[0]
        tempVorZen = 69.1  # set test-value
        txStr=","+str(tempVorZen)+","
        cmdList.append((0,[modules, regs, txCmdNr, txStr, tests]))
        pass

    elif a=="22":
        pass

    elif a=="23":
        pass

    elif a=="24":
        pass

    elif a=="30":  #  factory settings (parameter) - NOT in EEPROM -> after boot eeprom
        txCmdNr = 0x30  # reset all values to factory setting
        regs=[0]
        txStr=""
        cmdList.append((0.2,[modules, regs, txCmdNr, txStr, tests]))

    elif a=="31":  #  move valve reg1,2,3, time and direction
        txCmdNr = 0x31
        tMotOnMs,motDir,regs = get_motor_time()
        if tMotOnMs != 0:
            txStr = ","+str(tMotOnMs)+","+str(motDir)+','
            cmdList.append((0,[modules, regs, txCmdNr, txStr, tests]))

    elif a=="37":  #  receive jumper settings
        txCmdNr = 0x37
        regs=[0]
        txStr=""
        cmdList.append((0,[modules, regs, txCmdNr, txStr, tests]))

    elif a=="38":  # copy parameters EEPROM -> RAM
        txCmdNr = 0x38  
        regs=[0]
        txStr=""
        cmdList.append((0.2,[modules, regs, txCmdNr, txStr, tests]))

    elif a=="39":  # copy parameters RAM -> EEPROM
        txCmdNr = 0x39 
        regs=[0]
        txStr=""
        cmdList.append((0.2,[modules, regs, txCmdNr, txStr, tests]))

    elif a=="3A":  #  RESET using watchdog
        txCmdNr = 0x3A
        txStr=""
        cmdList.append((0,[modules, regs, txCmdNr, txStr, tests]))

    elif a=="3F":  # read motor current
        txCmdNr = 0x3F
        regs=[0]
        txStr = ""
        cmdList.append((0,[modules, regs, txCmdNr, txStr, tests]))

    elif a=="41":  #  receive jumper settings
        txCmdNr = 0x41
        txStr=""
        cmdList.append((0,[modules, regs, txCmdNr, txStr, tests]))

    elif a=="t1":  # read status1 -> set VLtemp -> wait -> read status1
        txCmdNr = 2  # regulator status 1
        regs=[1,2,3]
        txStr = ""
        cmdList.append((0,[modules, regs, txCmdNr, txStr, tests]))

        txCmdNr = 0x20  # set VLtemperature
        regs=[0]
        txStr=","+str(69.2)+","  # set test-value
        cmdList.append((1,[modules, regs, txCmdNr, txStr, tests]))

        txCmdNr = 2  # regulator status 1
        regs=[1,2,3]
        txStr = ""
        cmdList.append((0,[modules, regs, txCmdNr, txStr, tests]))
        pass

    elif a=="t2":  # get ticks -> reset wd -> wait -> get ticks
        txCmdNr = 0x37  # get ms-ticks
        regs=[0]
        txStr = ""
        cmdList.append((0,[modules, regs, txCmdNr, txStr, tests]))

        txCmdNr = 0x3A  # reset via watchdog - wait 10 sec
        regs=[0]
        txStr=""
        cmdList.append((15,[modules, regs, txCmdNr, txStr, tests]))

        txCmdNr = 0x37  # get ms-ticks
        regs=[0]
        txStr = ""
        cmdList.append((0,[modules, regs, txCmdNr, txStr, tests]))
        pass

    elif a=="t3":  # read all parameters
        txCmdNr = 0x5  # read parameter set 1
        regs=[0,1,2,3]
        txStr = ""
        cmdList.append((0,[modules, regs, txCmdNr, txStr, tests]))

        txCmdNr = 0x6  # read parameter set 2
        regs=[1,2,3]
        txStr=""
        cmdList.append((0,[modules, regs, txCmdNr, txStr, tests]))

        txCmdNr = 0x7  # read parameter set 3
        regs=[1,2,3]
        txStr = ""
        cmdList.append((0,[modules, regs, txCmdNr, txStr, tests]))
        pass

    elif a=="t4":  # start valve and read motor current
        tMotOnMs,motDir,regs = get_motor_time()
        regsa = regs

        txCmdNr = 0x3F  # read motor current
        txStr = ""
        regs=[0]
        cmdList.append((0,[modules, regs, txCmdNr, txStr, tests]))

        txCmdNr = 0x31  # move motor
        regs = regsa  # use selected regulator
        if tMotOnMs != 0:
            txStr = ","+str(tMotOnMs)+","+str(motDir)+','
            cmdList.append((0,[modules, regs, txCmdNr, txStr, tests]))


    elif a=="t5":  # check motor moving close->open and measure crrent
        global testMotors  # list [ (mod,reg), ...]
        mval=[]
        #'''
        for (mod,reg) in testMotors:
            rval=motor_test(mod,reg)
            mval.append(rval)
        save_mot_test(mval)
        #'''
        plot_mot_test(mval)

    elif a=="cp":  # change parameter
        smod = input("modul / 99:all 1+3 / 0:break ->")
        sreg = input("regler ->")
        scmd = input("cmd 5 6 7 (param-set 1,2,3) ->")
        parameterName =""
        tests = 1

        if smod == "99":
            modules = get_modules()
            regs=[1,3]

        elif smod=="0":
            result=[]
        
        modules, regs, cmd = select_modules(smod,sreg,scmd)



        if mod != 0:
            for mod in modules:
                for reg in regs:
                    change_parameter( mod, reg, cmd, parameterName )
            result=[]


    if a in implemented:
        mrcTotal=[]
        for cmd in cmdList:
            result,mrcList = do_test( fo, cmd[1])  # perform command
            mrcTotal.extend(mrcList)
            print("sleepeing %.2fsec"%(cmd[0]))
            time.sleep(cmd[0])
        if a=="t3":
            save_parameter(mrcTotal,fParsName)
        if a=="t4":
            while motOn:
                txCmdNr = 0x3F  # read motor current
                txStr = ""
                regs=[0]
                result,mrcList=do_test(fo,[modules, regs, txCmdNr, txStr, tests])
                print("motCurrent=",motCurrent)
                time.sleep(0.5)
                if motCurrent < 5:
                    motOn = 0
    return result



# active menu-selections
implemented = ["0","1","2","4","5","6","7",\
               "20","22","23","24","25",\
               "30","31","37","38","39","3A","3F",\
               "41",\
               "t1","t2","t3","t4","t5",\
               "cp"
               ]
def net_test_menu(fo,modules):
    regs    = [0]
    txStr   = ""
    tests   = 1
    antw=input("Press ENTER to skip, 1 ENTER to show Menu")
    if antw == "1":
        print()
        print(40*"=")
        print(" 0    Ende")
        print(" 1    Ping")
        print(" 2    read status values part 1")
        print(" 4    read status values part 2")
        print(" 5    read parameter: module / reg.part 1")
        print(" 6    read parameter: module / reg.part 2")
        print(" 7    read parameter: module / reg.part 3")
        print("20    hex,  send zentrale Vorlauftemperatur")
        print("22    hex,  send parameter for modul or regulator set 1 reg 1,2,3 !!! tVlRxValid double!!!")
        print("23    hex,  send parameter for regulator set 2")
        print("24    hex,  send parameter for regulator set 3")
        print("25    hex,  send parameter for regulator set 4 - special parameters")
        print("30    hex,  reset parameters to factory settings- NOT in EEPROM -> after boot eeprom")
        print("31    hex,  move valve reg1,2,3, time and direction")
        print("  34    hex,  set valve back to normal control / stop service mode / stop motors ")
        print("  35    hex,  set regulator to active / inactive")
        print("  36    hex,  fast mode on / off")
        print("37    hex,  read ms-timer value")
        print("38    hex,  copy all parameters from EEPROM to RAM")
        print("39    hex,  write all parameters from RAM to EEPROM")
        print("3A    hex,  RESET using watchdog; wait 10sec")
        print("  3B    hex,  clear eeprom  ??? plpl test eeprom if ram space is left")
        print("  3C    hex,  check if motor connected")
        print("  3D    hex,  open and close valve to store times")
        print("  3E    hex,  switch off current motor")
        print("3F    hex,  receive motor current")
        print("  40    hex,  LCD-light on/off")
        print("41    hex,  send jumper settings")
        print("Combined commands:")
        print("t1    rx status1, set VLtemp, rx status1")
        print("t2    get ms-tic > reset WD -> 15sec -> get ms-tic")
        print("t3    read all parameters to file")
        print("t4    move motor and read current")
        print("t5    check motor (set testMotors on top of file")
        print("cp    change parameter")
        print("     ")
        print(40*"-")
        a=""

    while True:
        a = input("select ->")
        if a == "0":
            return a
        if a in implemented:
            return a
        else:
            print("not implemented, try again - ", end="")


# -------------------------------------------------------------------
# -------------------------------------------------------------------
# -------------------------------------------------------------------
# -------------------------------------------------------------------
# -------------------------------------------------------------------
# -------------------------------------------------------------------
# -------------------------------------------------------------------
# -------------------------------------------------------------------

if __name__ == "__main__" :
    sErr,ser = ser_check()
    hostname = cg.hkr_obj._get_hostname()
    modules = get_modules()
    #modules = [2]
    testMotors = all_mod_regs( modules, [1,3] )
    #testMotors = [(2,1),(2,3)]
    tests = 1
    print(60*"=")
    print("hostname =",hostname)
    print("modules  =",modules)
    print("tests    =",tests)
    tempPath = "temp/"
    if not os.path.exists(tempPath):
        os.makedirs(tempPath)
    parsPath = "parameter/"
    if not os.path.exists(parsPath):
        os.makedirs(parsPath)
    ts=time.strftime('%Y%m%d-%H%M%S',time.localtime())
    filename = tempPath+"commTest_%s_%s.dat"%(hostname,ts)
    fParsName = parsPath+"params_%s_%s.dat"%(hostname,ts)
    fo = open(filename,"w")

    # send and receive a command directly
    
    # *** test communication
    while True:
        antw = net_test_menu(fo,modules)
        if antw=="0":
            break
        else:
            result=perform(antw,fo,modules,tests)
            #break  # remove for continuous menu
            if result==None:
                print("---> activate selected menu item !")
                break

    ser.close()
    fo.close()

    fin=open(filename,"r")
    filenameSum = filename.rstrip(".dat")+"_sum.dat"
    fos = open(filenameSum,"w")

    # *** evaluate results
    fos.write("---Sum - overview---\n")
    # *** read all data from file and sort into dictionary
    # form: { "m1r3":[n,tmin,tmax,tsum,nErr,orErr], ... }
    mrd={}  # module-regulator-directory
    for line in fin:
        if line[0] != "[":
            continue
        #print(line)
        l0 = line.strip()
        # form of l1: [[txMod,txReg,t0,t1,rxErr]]
        l1 = ast.literal_eval(l0)
        for d in l1:
            t0=d[2]
            t1=d[3]
            dt = t1-t0
            id = "m%dr%d"%(d[0],d[1])
            if id in mrd:
                #[n,tmin,tmax,tsum,nErr,orErr]
                mrd[id][0] += 1
                if dt < mrd[id][1]:
                    mrd[id][1]=dt
                if dt > mrd[id][2]:
                    mrd[id][2]=dt
                mrd[id][3] += dt
                if d[4] != 0 :
                    mrd[id][4] += 1
                mrd[id][5] |= d[4]
            else:
                # add mod/reg to directory 
                e=0
                if d[4] != 0:
                    e=1
                mrd[id] = [1,dt,dt,dt,e,d[4]]

    for id in mrd:
        hs   = id.split("r")
        mod  = int(hs[0][1:])
        reg  = int(hs[1])
        n    = mrd[id][0]
        min  = mrd[id][1]
        max  = mrd[id][2]
        sum  = mrd[id][3]
        nErr = mrd[id][4]
        orErr= mrd[id][5]
        hs="Mod %02d Reg %d: n=%d min=%5.3fs mitt=%5.3fs max=%5.3fs nErr=%2d orErr=%04X"%\
            (mod,reg,n,min,sum/n,max,nErr,orErr )
        print(hs)
        fos.write(hs+"\n")

    '''
    '''
    fos.close()
    pass






