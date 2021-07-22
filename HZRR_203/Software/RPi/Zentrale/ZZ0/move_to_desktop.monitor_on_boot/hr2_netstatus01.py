#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
hr2_netstatus
send and receive commands permanently and make statistics
to find networking problems
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


def get_modules():
    antwort = hkr_cfg.get_heizkreis_config(0,1)
    return( antwort[1] )

def all_mod_regs(mods,regs):
    ''' return list with all modules (m,0) or all regs (m,1)..(m,3)'''
    # regs = [0,1,2,3] or part of it
    lAll=[]
    for mod in mods:
        for r in regs:
            lAll.append( (mod,r) )
    print(lAll)
    return lAll



serTimeout = 0.3
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
            timeout     = serTimeout
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
            time.sleep(1.0)
        print("rs485 Netz verbunden")
    return err, ser




def txrx_Command_2( txCmd ):
    if type(txCmd)==str :
        txCmd = txCmd.encode()  # byte-array needed for serial comm.
    ser.reset_output_buffer()
    ser.reset_input_buffer()
    #print("send command:",txCmd)
    ser.write(txCmd)       # send command
    ''' # same with exception handling
        try:
            self.ser.write(self.txCmd)                  # start writing string
        except serial.SerialTimeoutException as e:
            vor.vorlaut( 2, "07 timeout sending string: %s"%(self.txCmd))
            vor.vorlaut( 2,  "  exception = %s"%(e))
        except serial.SerialException as e:
            vor.vorlaut( 2,  "08 SerialException on write")
            vor.vorlaut( 2,  "   exception = %s"%(e))
            self.ser.close()
        except Exception as e:
            vor.vorlaut( 2,  "09 error serial port %s, writing"%(self.serPort))
            vor.vorlaut( 2,  "   exception = %s"%(e))
            self.ser.close()
    '''
    # ??? not needed? ser.flush()  # send out tx-buffer 
    while ser.out_waiting : # block until whole command is sent
        pass
    rxDatB = ser.readline()
    rxDat = rxDatB.decode()
    return rxDat



def comm_check( txDat, rxDat):
    (txMod,txReg,txCmdNr) = txDat
    RXE_SHORT     = 0x0001
    RXE_VALUE     = 0x0002
    RXE_HEADER    = 0x0004
    RXE_ADR       = 0x0008
    RXE_CMD       = 0x0010
    RXE_MOD       = 0x0020
    RXE_REG       = 0x0040
    RXE_PROT      = 0x0080
    RXE_CHECK     = 0x0100  # wrong checksum or RLL
    RXE_NAK       = 0x0101  # no acknkwledge

    # *** analyze answer string
    # checksum and modbus LLR:
    rxErr=0
    # analyze length
    if ((rxDat=="") or (len(rxDat) < 9)):
        print("received data trash. string too small:")
        rxErr |= RXE_SHORT
        return rxErr
    else:
        # analyze checksums
        checksum, rxStr = mb.unwrap_modbus( rxDat )
        if not checksum :
            rxErr |= RXE_CHECK
            return rxErr
        if not ("ACK" in rxStr) :  # in case of ping-command
            rxErr |= RXE_NAK
            return rxErr
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
            return rxErr
        except Exception as e:
            print("error:", e)
            rxErr |= RXE_HEADER
            return rxErr
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
        return rxErr



# -------------------------------------------------------------------


if __name__ == "__main__" :
    hostname = cg.hkr_obj._get_hostname()
    modules = get_modules()
    print(60*"=")
    print("hostname =",hostname)
    print("modules  =",modules)

    ts=time.strftime('%Y%m%d-%H%M%S',time.localtime())
    
    filename = "log/commTest_%s_%s.dat"%(hostname,ts)
    fo = open(filename,"w")

    # send and receive a command directly
    sErr,ser = ser_check()
    modules = [1,2,30]

    # *** test communication
    txCmdNr = 1  # ping
    txReg   = 0
    txStr   = ""
    tests   = 1000
    result=[]
    for txMod in modules:
        res=[]
        print(txMod,end=":")
        for test in range(tests):
            print(".",end="")
            txCmd = mb.wrap_modbus( txMod, txCmdNr, txReg, txStr )
            t0 = time.time()
            rxDat = txrx_Command_2( txCmd )
            t1 = time.time()
            #print("string received:", rxDat, end="  ")
            #print("delay:",t1-t0, end="  ")
            txDat = (txMod,txReg,txCmdNr)
            rxErr = comm_check(txDat,rxDat)
            #print("check result: %04X"%(rxErr))
            res.append([txMod,t0,t1,t1-t0,rxErr])
        result.append(res)
        fo.write(str(res)+"\n")
        print()

    ser.close()
    fo.close()
    #print("result=",result)

    # *** evaluate results
    for res in result:
        mod = res[0][0]
        min=100.0
        max=0.0
        sum=0
        n=0
        errCnt = 0
        for m in res:
            #print(m)
            dt = m[3]
            if dt < min:
                min = dt
            if dt > max:
                max = dt
            sum += dt
            n += 1
            if m[4] > 0:
                errCnt +=1
        print("Modul %2d: n=%d min=%5.3fs mitt=%5.3fs max=%5.3fs err=%d"%(mod,n,min,sum/n,max,errCnt ))


    pass






