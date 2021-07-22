#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
hr2_ser485.py

Send and receive commands and data via RS485 bus
"""
import serial
import time
import configparser

#import modbuas_b as mb


def get_hr2_config( item ):
    ''' read parameeter from "hz_rr_config.ini" '''
    ''' item:'''
    '''   0 : read path of file containing hostname''' 
    '''   1 : read RaspberryPi-3 USB-Serial<->RS485 converter port'''
    '''   2 : read RaspberryPi-4 USB-Serial<->RS485 converter port'''
    '''  11 : read baudrate'''
    '''  12 : read serial timeout ??? '''
    '''  15 : read serial timout waiting for input'''
    hr2ConfFileName = "config/hz_rr_config.ini"
    hr2Conf = configparser.ConfigParser()   # parameters for all modules
    hr2Conf.read(hr2ConfFileName)
    answer = None
    if hr2Conf == []:
        statRs485['iniFile'] = "missing"
    else:
        statRs485['iniFile'] = "ok"
        try:
            if item == 0:
                answer = hr2Conf['system']['hostPath']
            elif item == 1:
                answer = hr2Conf['system']['serialPort_PIthree']
            elif item == 2:
                answer = hr2Conf['system']['serialPort_PIfour']
            elif item == 11:
                answer = int(hr2Conf['SerialBus']['ser_bus_baud_rate'])
            elif item == 12:
                answer = float(hr2Conf['SerialBus']['ser_bus_timeout'])
            elif item == 15:    
                answer = float(hr2Conf['SerialBus']['ser_bus_rx_timeout'])
        except Exception as e:
            statRs485['iniFile'] = "key!"
        return answer        
    



# ----------------------------------------
# USB-RS485 serial bus connection
# ----------------------------------------


statRs485 = {         # usb-rs485 interface connection
    'iniFile' : "no", # or e{"ok","missing","key!"} 
    'connect' : "no", # or e{"fail","init","close","open","connected"};
    'rxBuffer': "no", # or e{"clear","unknown"}
    'txBuffer': "mp", # or e{"clear","unknown"} 
    }
    

def ser_instance() :
    ''' initialize serial port and set serial parameters'''
    ''' return error nr. (0=ok) and serial handle '''
    try:
        serPort = get_hr2_config(2)  # RPi4 fixed port path
        baudrate = get_hr2_config(11)
        serTimeout = get_hr2_config(12)
    except:
        statRs485["iniFile"] = "missing"
        ser = None
    else:
        try:
            ser = serial.Serial(
                port        = serPort,
                baudrate    = baudrate,
                parity      = serial.PARITY_NONE,
                stopbits    = serial.STOPBITS_TWO,
                bytesize    = serial.EIGHTBITS,
                timeout     = serTimeout
                )
            statRs485['connect'] = "init"
            statRs485["iniFile"] = "ok"
 
        except serial.SerialException as e:
            statRs485['connect'] = "fail"
            ser = None
        except Exception as e:
            statRs485['connect'] = "fail"
            ser = None
    return ser


def ser_open():
    ''' connect to serial port - from set up in ser_instance()'''
    ''' return error, 0=ok'''
    ser = ser_instance()
    try:
        ser.open() # open USB->RS485 connection
        statRs485['connect'] = "open"
    except serial.SerialException as e:
        if "Port is already open" in e.args[0]:
            statRs485['connect'] = "open"
        else:
            statRs485['connect'] = "close"
    except  Exception as e:
        ser.close()
        statRs485['connect'] = "close"
    return ser


def ser_close(ser):
    ''' close serial port ser '''
    ser.close()
    statRs485['connect'] = "close"
    

def ser_clear_buffer(ser):
    ''' clear tx and rx buffers; usually before a transmission ''' 
    ''' return 0:ok, error if clear was not possible '''
    answ=0
    try:
        ser.reset_output_buffer()
        statRs485['txBuffer'] = "clear"
    except:
        statRs485['txBuffer'] = "clear"
        answ=1
    try:        
        ser.reset_input_buffer()
        statRs485['rxBuffer'] = "clear"
    except serial.SerialException as e:
        statRs485['rxBuffer'] = "clear"
        answ=2
    return answ


def ser_check(ser):
    ''' Check if serial RS485 port is active, open it if not '''
    if ser==None or ser.isOpen() == False :
        ser=ser_open()
        time.sleep(0.1)
        ser_clear_buffer(ser)
        return ser


# ----------------------------------------
# dialog via RS485 serial with modules
# ----------------------------------------
'''
Master - Slave  Dialog
Master: Raspberry Pi or another Linux computer
Slaves: Modules
+ Master sends a command string and slave anwers within a max delay
+ If nothing is received (rx) within this timeout None is returned
  Otherwise an unpacked recieved string is returned
+ The answer is checked if it comes from the called module and if
  it contains data for the correct regulator/module and command.
  if the answer does not meet teh called data, None is returned.
+ All data is packed with packet information, checksum and LLR Byte
'''


def checksum( s ) :
    ''' calculate a 16Bit checksum of all bytes of s '''
    ''' s   binary array like:  b'xxx' '''
    cs = 0
    for c in s :
        cs += ord(c)
    cs = cs & 0xFFFF    # make unsigned 16 bit
    return cs


def lrc_parity( s ) :
    ''' calculate a 8Bit LRC parity over all bytes of s '''
    ''' s   binary array like:  b'xxx' '''
    lrc = 0
    for c in s :
       lrc = lrc ^ ord(c)
    lrc = lrc & 0x00FF
    return lrc


def wrap_modbus( adr, fnc, contr, cmdstr ) :
    ''' generates complete command from input '''
    # adr      module address
    # fnc      function number
    # contr    regulator number 1,2,3,4 or 0 for module
    # cmdstr   command string ; could be "" (empty string)
    # return:  byte array
    PROT_REV ="b"
    try:
        cmd = "%02X%02X%1X%s%s"%\
            (int(adr), int(fnc), int(contr), PROT_REV, str(cmdstr) )
        cs = checksum( cmd )
        cmd = "%s%04X"%(cmd,cs)
        lrc = lrc_parity( cmd )
        cmd = ":%s%02X\r\n"%(cmd, lrc)
        cmd.encode()     # make byte-array
    except Exception as e:
        cmd = "ERROR_WRAPPING_MODBUS"
        print("wrap_modbus exception:",e)
    return cmd




RX_TIMEOUT = 0.0

# *** pack command strings
def txrx_command( ser, txCmd ):
    global RX_TIMEOUT
    ser_check(ser)
    if type(txCmd) == str :
        txCmd = txCmd.encode()   # force to array of bytes
    ser_clear_buffer(ser)
    try:
        ser.write(txCmd)
    except serial.SerialTimeoutException as e:
        print( 2, "07 timeout sending string: %s"%(self.txCmd))
        print( 2,  "  exception = %s"%(e))
        line=""    # nothing sent
    except serial.SerialException as e:
        print()( 2,  "08 SerialException on write")
        print( 2,  "   exception = %s"%(e))
        ser.close()  # close to reopen it next time
        line=""    # nothing sent
    except Exception as e:
        print( 2,  "09 error serial port %s, writing"%(self.serPort))
        print( 2,  "   exception = %s"%(e))
        ser.close()  # close to reopen it next time
        line=""    # nothing sent

    time.sleep(0.05)  # wati for device being ready to transmit
    ser.flush()
    #ser.reset_input_buffer()  # ??? might delete part of answer
    rxCmd = ""
    if RX_TIMEOUT == 0.0 :
        RX_TIMEOUT = get_hr2_config(15)
    et = time.time() + RX_TIMEOUT  # timeout waiting for answer
    l0=b""
    while (time.time() < et) and (l0==b""):
        l0 = ser.readline()
        #print(time.time()," < ", et,":", (time.time() < et),"~",l0)
    print("l0=",l0)
    l1 = l0.split(b":")
    print("rx l1=",(l1))
    if(len(l1)==2):
        line = l1[1]
    else:
        line = b""
    '''
    line = line.strip()   # remove white-spaces from either end
    try:
        line = line.decode()     # make string
    except UnicodeDecodeError as e:
        self.dbg.m("!!! UnicodeDecodeError:",e,cdb=1)
    except Exception as e:
        # some false byte in byte-array
        vor.vorlaut( 2,  "10 cannot decode line")
        vor.vorlaut( 2,  "   exception = %s"%(e))
        line = ""
        pass
    self.dbg.m("line=",line,cdb=1)
    st.rxCmd    = line
    self.rxCmd  = line #reset after read?
    pan.pa_to_ser_obj.add('txrx_command -> self.rxCmd: ' + str(self.rxCmd))
    '''
    return line






    return "xxx"




# ----------------------------------------
# ----------------------------------------

if __name__ == "__main__":
    print("**********************************")
    print("hr2_ser485")
    print("handle rs485 bus communication")
    print("**********************************")

    '''
    print("USB-port on RPi3:  ",get_hr2_config(1))
    print("USB-port on RPi4:  ",get_hr2_config(2))
    ser = ser_open()
    
    print( "connect,iniFile =",statRs485["connect"],statRs485["iniFile"] ) 
    '''
    ser=ser_check(None)

    txcmd=wrap_modbus(1,1,0,"") 
    print("txcmd =",txcmd)
    rxcmd = txrx_command(ser, txcmd)
    print("rxcmd =", rxcmd)

    ser_close(ser)
    

    
