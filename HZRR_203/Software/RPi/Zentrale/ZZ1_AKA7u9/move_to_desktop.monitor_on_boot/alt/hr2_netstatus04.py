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

motCurrent = 0

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
                motCurrent = -99
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







def save_parameter( mrcTotal,fParsName):
    ''' fit read parameters to their variable names and save them to file '''
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
    mrcTotal.sort()
    pars={}  # fill in all modules
    par={}   # fill in parameters of a module with its regulators
    for mrc in mrcTotal:
        '''
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

    return 0








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

    elif a=="t1":
        txCmdNr = 2  # regulator status 1
        regs=[1,2,3]
        txStr = ""
        cmdList.append((0,[modules, regs, txCmdNr, txStr, tests]))

        txCmdNr = 0x20  # seet VLtemperature
        regs=[0]
        txStr=","+str(69.2)+","  # set test-value
        cmdList.append((1,[modules, regs, txCmdNr, txStr, tests]))

        txCmdNr = 2  # regulator status 1
        regs=[1,2,3]
        txStr = ""
        cmdList.append((0,[modules, regs, txCmdNr, txStr, tests]))
        pass

    elif a=="t2":
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
        cmdList.append((0.5,[modules, regs, txCmdNr, txStr, tests]))

        txCmdNr = 0x31  # move motor
        regs = regsa  # use selected regulator
        if tMotOnMs != 0:
            txStr = ","+str(tMotOnMs)+","+str(motDir)+','
            cmdList.append((0,[modules, regs, txCmdNr, txStr, tests]))

        motOn=True


    if a in implemented:
        mrcTotal=[]
        for cmd in cmdList:
            result,mrcList = do_test( fo, cmd[1])
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
               "20",\
               "31","37","3A","3F",\
               "41",\
               "t1","t2","t3","t4"]
def net_test_menu(fo,modules):
    regs    = [0]
    txStr   = ""
    tests   = 1
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
    print("  22    hex,  send parameter for modul or regulator set 1 reg 1,2,3 !!! tVlRxValid double!!!")
    print("  23    hex,  send parameter for regulator set 2")
    print("  24    hex,  send parameter for regulator set 3")
    print("  25    hex,  send parameter for regulator set 4 - special parameters")
    print("  30    hex,  reset parameters to factory settings")
    print("31    hex,  move valve reg1,2,3, time and direction")
    print("  34    hex,  set valve back to normal control / stop service mode / stop motors ")
    print("  35    hex,  set regulator to active / inactive")
    print("  36    hex,  fast mode on / off")
    print("37    hex,  read ms-timer value")
    print("  38    hex,  copy all parameters from EEPROM to RAM")
    print("  39    hex,  write all parameters from RAM to EEPROM")
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
    hostname = cg.hkr_obj._get_hostname()
    #modules = get_modules()
    modules = [1]
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
    sErr,ser = ser_check()
    
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
        if line[0]=="#":
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






