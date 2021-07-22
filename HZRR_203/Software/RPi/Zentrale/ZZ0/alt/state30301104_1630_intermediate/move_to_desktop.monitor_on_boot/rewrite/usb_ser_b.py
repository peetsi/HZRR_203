#!/usr/bin/env python3
# -*- coding: utf-8 -*-



import time

import serial

import hr2_parse_answer as pan
import modbus_b as mb
import vorlaut as vor
from hr2_variables import *
import hz_rr_config as cg
import time as ti
import inspect as it

class Serbus:
    ser=port=baudrate=parity=stopbits=bytesize=timeout=None
    cmdHead=tic=ticStr=vlMeas=rlMeas=vlEff=rlEff=vlrl=dateTime=header= \
        cn2=cn4=txCmd=ps=p=read_stat_str=rxCmd=rxCmdLast=connected= \
            blocked=blockTTL=blockSince=calledBy=blockedBy= None
    
    def __init__(self,serT=0.5,rxT=2.5,netR=3):
        self.SER_TIMEOUT = serT
        self.RX_TIMEOUT  = rxT
        self.NET_REPEAT  = netR
        self.baudrate    = 115200
        self.serPort     = cg.conf_obj.r('system','serialPort' ) #"COM5"
        self.blocked     = False
        self.blockedBy   = "" # name of the script which did block us - so only him or TTL can unblock
        self.blockTTL    = 2.0 # seconds
        self.blockSince  = 0.0 # seconds
        #self.ser_check()
        #self.ser_open()

    def block(self, byWHO=""):
        curframe = it.currentframe()
        calframe = it.getouterframes(curframe, 2)
        self.calledBy = calframe[1][3]
        print('[USB_SER_B.PY][BLOCK][CALLEDBY]{', self.calledBy,"}")
        if self.blocked == False:
            self.blockedBy = byWHO
            self.blocked = True
            self.blockSince = ti.perf_counter()
        else: 
            print("already blocked.. checking for validity")
            #print("for a debug print, printing entire object:")
            #print(self)
        return self.blockValidity()

    def unblock(self, byWHO=""):
        curframe = it.currentframe()
        calframe = it.getouterframes(curframe, 2)
        self.calledBy = calframe[1][3]
        if self.block == False: return print("[USB_SER_B.PY][UNBLOCK][CALLEDBY] {",self.calledBy,"}")
        if (self.blockedBy != "" and (self.blockedBy==byWHO or byWHO=="BLOCKVALMASTERKEY")):
            self.blocked = False
            self.blockSince = 0.0 #reset values
        elif (self.blockedBy != "" and self.blockedBy != byWHO):
            print("sorry you do not have  the rights to unblock. blockedby:",self.blockedBy,";unlock tried by:", byWHO)
        else:
            print("block without special permissions lifted")
            self.blocked = False
            self.blockSince = 0.0
        
        return self.blockValidity


    def blockValidity(self): #check if the block is still valid by the TTL
        if (not self.blocked): # not blocked
            self.blocked = False
            return self.blocked #print("not blocked, no validity required")
        now = ti.perf_counter()
        if ((now - self.blockSince) > self.blockTTL):
            print("TTL has been passed - assuming that a function has crashed - the block status of the function will be lifted.")
            self.unblock("BLOCKVALMASTERKEY")
        else:
            #print("TTL has not been passed but function has been tried to access")
            return 

    def blockStatus(self, waitForUnblock=1):
        self.blockValidity()
        if (waitForUnblock and self.blocked):
            t = time.perf_counter()
            print("amma blocked. waiting for unblock - freezing self.blocked:", self.blocked, ";blockduration:", (t-self.blockSince))
            while ((t-self.blockSince)<self.blockTTL):
                self.blockValidity()
                if self.blocked == False: return False # is unblocked, exit
                ti.sleep(0.1)
                #print("waiting for function to unblock")
        else:
            return self.blocked

    def ser_instant(self) :
        if (self.blockStatus()): return 8 # blocked
        #self.block()
        #if self.connected > 0: return 9    #already connected
        err=0
        try:
            self.ser = serial.Serial(
                port        = self.serPort,
                baudrate    = self.baudrate,
                parity      = serial.PARITY_NONE,
                stopbits    = serial.STOPBITS_TWO,
                bytesize    = serial.EIGHTBITS,
                timeout     = self.SER_TIMEOUT)
        except serial.SerialException as e:
            vor.vorlaut( 3,  "01 cannot find: %s"%(self.serPort))
            vor.vorlaut( 3,  "   exception = %s"%(e))
            err = 1
        except Exception as e:
            vor.vorlaut( 3,  "02 something else is wrong with serial port: %s"%(self.serPort))
            vor.vorlaut( 3,  "   exception = %s"%(e))
            err = 2
        self.unblock()
        return err

    def ser_open(self):
        if (self.blockStatus()): return 8 # blocked
        self.block()
        #if self.connected != 0: return 9    #already connected
        err=0
        try:
            self.ser.open() # open USB->RS485 connection
            self.connected = 1
        except serial.SerialException as e:
            vor.vorlaut( 3,  "03 cannot open: %s"%(self.serPort))
            vor.vorlaut( 3,  "   exception = %s"%(e))
            err = 3
        except  Exception as e:
            vor.vorlaut( 3,  "04 something else is wrong with serial port:"%(self.serPort))
            vor.vorlaut( 3,  "   exception = %s"%(e))
            err = 4
        self.connected = 0
        self.unblock()
        return err


    def ser_reset_buffer(self):
        #if (self.blockStatus()): return 8 # blocked
        #self.block()
        #if self.connected != 0: return 9    #already connected
        err=0
        try:
            self.ser.flushOutput()  # newer: ser.reset_output_buffer()
            self.ser.flushInput()   # newer: ser.reset_input_buffer()
        except serial.SerialException:
            err = 5
            vor.vorlaut( 3,  "05 cannot erase serial buffers")
            vor.vorlaut( 3,  "   exception = %s"%(e))
        except Exception as e:
            err = 6
            vor.vorlaut( 3,  "06 something else is wrong with serial port: %s"%(self.serPort))
            vor.vorlaut( 3,  "   exception = %s"%(e))
        #self.unblock()
        return err

    def ser_check(self):
        #if self.connected != 0: return 9    #already connected
        if (self.blockStatus()): return 8 # blocked
        self.ser_instant()
        if self.ser.isOpen() == False :
            self.connected=0
            print("open network")
            err = 0
            err |= self.ser_open()
            if( err ) :
                print("rs485 Netz: %d"%(err))
            time.sleep(1.0)
            self.ser_reset_buffer()
        print("rs485 Netz verbunden")
        self.connected=1
        self.unblock()


    def txrx_command(self, txCmd ) :
        blockkey="TXRX_COMMAND_BLOCK"
        if (self.blocked==True and self.blockedBy==blockkey):
            return print("[USB_SER_BUS_B][TXRX_COMMAND] you can't call this function while it is still working. please wait.")
        # if (self.blockStatus()): return 8 # blocked
        #        self.block()
        self.block(blockkey)
        # send a command and receive answer
        # txCmd      byte-array of command-string
        # return:    string with command
        twait1 = 0.01
        twait2 = 0.01
        self.ser.flushOutput()
        #vor.vorlaut( 2, "\ntx: %s"%(txCmd[:-2]))

        if type(self.txCmd)==str :
            self.txCmd = self.txCmd.encode()
        try:
            self.ser.write(self.txCmd)                  # start writing string
        except serial.SerialTimeoutException as e:
            vor.vorlaut( 2, "07 timeout sending string: %s"%(self.txCmd))
            vor.vorlaut( 2,  "  exception = %s"%(e))
        except serial.SerialException as e:
            vor.vorlaut( 2,  "08 SerialException on write")
            vor.vorlaut( 2,  "   exception = %s"%(e))
            self.ser.close()
        except   Exception as e:
            vor.vorlaut( 2,  "09 error serial port %s, writing"%(self.serPort))
            vor.vorlaut( 2,  "   exception = %s"%(e))
            self.ser.close()

        self.ser.flush()
        self.ser.flushInput()
        st.rxCmd = ""
        self.rxCmdLast=self.rxCmd
        self.rxCmd=""
 
        #time.sleep( twait1 )   # maybe not necessary: flush waits unitl all is written
        # using USB-RS485 converter: no echo of sent data !
        # receive answer from module
        et = time.time() + self.RX_TIMEOUT 
        l0=b""
        while (time.time() < et) and (l0==b""):
            l0 = self.ser.readline()
            #print(time.time()," < ", et,":", (time.time() < et),"~",l0)
        #print("l0=",l0)
        l1 = l0.split(b":")
        #print("rx l1=",(l1))
        if(len(l1)==2):
            line = l1[1]
        else:
            line = b""
        line = line.strip()   # remove white-spaces from either end
        try:
            line = line.decode()     # make string
        except Exception as e:
            # some false byte in byte-array
            vor.vorlaut( 2,  "10 cannot decode line")
            vor.vorlaut( 2,  "   exception = %s"%(e))
            line = ""
            pass
        print("line=",line)
        st.rxCmd    = line
        self.rxCmd  = line #reset after read?
        self.unblock(blockkey)
        return line


    def net_dialog(self, txCmd, info=0 ):
        self.block()
        maxCnt = self.NET_REPEAT
        repeat = 0
        ready  = False
        while repeat < maxCnt :
            self.ser_reset_buffer()
            self.txrx_command( txCmd )
            self.unblock()
            #print(pan.parse_answer())
            if pan.parse_answer():
                if info==0:
                    #self.unblock()
                    return True#, repeat
                #self.unblock()
                return True, repeat
            else:
                repeat += 1
        if info==0: 
            #self.unblock()
            return False#, repeat
        #self.unblock()
        return False, repeat

    # *****************************************
    # *** module communication commands     ***
    # *****************************************

    def ping(self, modAdr ):
        if (self.blockStatus()): return 8,8 # blocked
        self.block()
        self.txCmd = mb.wrap_modbus( modAdr, 1, 0, "" )   # cmd==1: send ping
        return self.net_dialog(self.txCmd, 1)

    def read_stat(self, modAdr, subAdr ) :
        if (self.blockStatus()): return 8 # blocked
        ''' read all status values from module
            using command 2 and 4
        '''
        # modAdr e {1..31}
        # subAdr e {0..3} for {module, reg0, reg1, reg2}
        block_name = "USB_SER_B_READ_STAT_UNINTERRUPTABLE"
        self.block(block_name)
        # *** first part, scan to cn2
        self.txCmd = mb.wrap_modbus( modAdr, 2, subAdr, "" )
        if not  self.net_dialog(self.txCmd):
            return False
        
        time.sleep(0.5)
        
        # *** second part, scan to cn4
        self.txCmd = mb.wrap_modbus( modAdr, 4, subAdr, "" )
        if not  self.net_dialog(self.txCmd):
            return False

        #read_stat(mod,reg)     # result is in cn2 and cn4
        self.get_milisec(modAdr)
        self.get_jumpers(modAdr)
        # *** print data
        #print("="*40)
        #print("cn2=",cn2)
        #print("cn4=",cn4)
        #print("timestamp ms=",st.rxMillis)
        #print("Jumper settings=%02x"%(st.jumpers))
        #print("-"*40)
        # module data:
        self.cn2      = cn2
        self.cn4      = cn4
        self.cmdHead  = "0002%02X%db "%(modAdr,subAdr)
        self.tic      = float(st.rxMillis) / 1000.0
        self.ticStr   = "t%.1f "%(self.tic)

        #cn2={"SN":0,"VM":0,"RM":0,"VE":0,"RE":0,"RS":0,"PM":0}
        self.vlMeas   = float(cn2["VM"])
        self.rlMeas   = float(cn2["RM"])
        self.vlEff    = float(cn2["VE"])
        self.rlEff    = float(cn2["RE"])
        self.rlSoll   = float(cn2["RS"])
        self.posMot   = float(cn2["PM"])

        #cn4={"ER":0,"FX":0,"MT":0,"NL":0} # command names
        self.erFlag  = int(cn4["ER"])
        self.fixPos  = float(cn4["FX"])
        self.motTime = float(cn4["MT"])
        self.nLimit  = int(cn4["NL"])

        s1    = "VM%5.1f RM%5.1f VE%5.1f RE%5.1f "%(self.vlMeas,self.rlMeas,self.vlEff,self.rlEff)
        s2    = "RS%5.1f P%03.0f "%(self.rlSoll, self.posMot)
        s3    = "E%04X FX%.0f M%.0f A%d"%(self.erFlag,self.fixPos,self.motTime,self.nLimit)
        # FX muss noch übersetzt werden.
        x = s1 + s2 + s3
        self.read_stat_str = str(self.cmdHead) + str(self.ticStr) + str(self.cn2["SN"]) + " " + str(x)
        print ("READ_STAT_STR:", self.read_stat_str)
        self.unblock(block_name)
        return self.read_stat_str

    def get_param(self, modAdr,subAdr):
        if (self.blockStatus()): return 8 # blocked
        self.block()
        '''read module-related parameter set from module'''
        if subAdr in [0,1,2,3]:
            self.txCmd = mb.wrap_modbus( modAdr, 0x05, subAdr,"" )
            if not  self.net_dialog(self.txCmd):
                self.unblock()
                return False
            elif subAdr == 0:
                self.unblock()
                return True

            self.txCmd = mb.wrap_modbus( modAdr, 0x06, subAdr,"" )
            if not  self.net_dialog(self.txCmd):
                return False
        
            self.txCmd = mb.wrap_modbus( modAdr, 0x07, subAdr,"" )
            if self.net_dialog(self.txCmd):
                return True

        self.unblock()
        return False


    def send_Tvor(self, modAdr,tempSend):
        if (self.blockStatus()): return 8 # blocked
        self.block()
        '''send Vorlauftemperatur to module'''
        self.txCmd = mb.wrap_modbus(modAdr,0x20,0,','+str(tempSend)+',')
        if self.net_dialog(self.txCmd):
            return True
        return False


    def send_param(self, modAdr,subAdr):
        if (self.blockStatus()): return 8 # blocked
        self.block()
        ''' send module parameters to module nr. modAdr
            0: module, 1,2,3: regulator
        '''
        if subAdr == 0:
            '''
            //           1         2         3         4         5         6  
            //  1234567890123456789012345678901234567890123456789012345678901234
            //  :02200b 111 222 33 44.4 55.5 66.6 77.7 88 99.9 0.5 02634Ccl0"    max. length
            e.g.:    010 060 10 40.0 75.0 32.0 46.0 15 20.0 0.5 
            // with:        typ.value   use    
            //   :02200b    header;     placeholder
            //   111        10 ms;      timer1Tic; 
            //   222        60 sec;     tMeas; measruring interval
            //   33         10 min;     dtBackLight; time for backlight on after keypressed
            //   44.4       degC;       tv0;   Kurve
            //   55.5       degC;       tv1
            //   66.6       degC;       tr0
            //   77.7       degC;       tr1
            //   88         15 min;     tVlRxValid  
            //   99.9       20 degC;    tempZiSoll
            //   0.5        0.5 degC;   tempTolRoom
            //   02634Ccl0  trailer - placeholder; cl0=="\r\n\0" (end of line / string)
            '''
            self.p = parameters[modAdr]
            s = ",%03d,%03d,%02d,%4.1f,%4.1f,%4.1f,%4.1f,%02d,%4.1f,%3.1f,"%( \
                self.p["timer1Tic"], self.p["tMeas"], self.p["dtBackLight"], self.p["tv0"], \
                self.p["tv1"], self.p["tr0"], self.p["tr1"], self.p["tVlRxValid"], \
                self.p["tempZiSoll"], self.p["tempZiTol"] )
            #print("s=",s)
            self.txCmd = mb.wrap_modbus( modAdr, 0x22, subAdr, s )
            #print(txCmd)
            if self.net_dialog(self.txCmd):
                return True
            return False

        elif subAdr in [1,2,3]: # parameter regulator, part 1,2,3
            # send:
            #   active, motIMin, motIMax, tMotDelay, tMotMin, tMotMax,
            #   dtOpen, dtClose, dtOffset
            time.sleep(0.2)
            self.ps = parameters[modAdr]["r"][subAdr]
            s = ",%d,%d,%d,%d,%d,%d,%d,%d,%d,"%(\
                self.ps["active"], self.ps["motIMin"], self.ps["motIMax"], self.ps["tMotDelay"],\
                self.ps["tMotMin"], self.ps["tMotMax"],\
                self.ps["dtOpen"], self.ps["dtClose"], self.ps["dtOffset"] )
            #print("s=",s)
            self.txCmd = mb.wrap_modbus( modAdr, 0x22, subAdr, s )
            #print(txCmd)
            if not self.net_dialog(self.txCmd):
                return False

            # send:
            #   pFakt, iFakt, dFakt, tauTempVl, tauTempRl, tauM
            time.sleep(0.2)
            s = ",%5.3f,%5.3f,%5.3f,%6.2f,%6.2f,%6.2f,"%(\
                self.ps["pFakt"], self.ps["iFakt"], self.ps["dFakt"], self.ps["tauTempVl"],\
                self.ps["tauTempRl"], self.ps["tauM"] )
            #print("s=",s)
            self.txCmd = mb.wrap_modbus( modAdr, 0x23, subAdr, s )
            #print(txCmd)
            if not self.net_dialog(self.txCmd):
                return False

            # send:
            #   m2hi, m2lo,
            #   tMotPause, tMotBoost, dtMotBoost, dtMotBoostBack, tempTol
            time.sleep(0.2)
            s = ",%5.3f,%5.3f,%d,%d,%d,%d,%3.1f,"%(\
                self.ps["m2hi"], self.ps["m2lo"], self.ps["tMotPause"], self.ps["tMotBoost"],\
                self.ps["dtMotBoost"], self.ps["dtMotBoostBack"], self.ps["tempTol"] )
            #print("s=",s)
            self.txCmd = mb.wrap_modbus( modAdr, 0x24, subAdr, s )
            #print(txCmd)
            if self.net_dialog(self.txCmd):
                return True
            return False


    def set_motor_lifetime_status(self,modAdr,subAdr):
        if (self.blockStatus()): return 8 # blocked
        self.block()
        ''' send the regulator motor lifetime status values to module nr. modAdr
            subAdr 1,2,3: regulator 1,2,3, reg-index 0,1,2,
        '''
        if subAdr in [1,2,3]: # parameter regulator
            # send:
            #   tMotTotal, nMotLimit
            self.ps = parameters[modAdr]["r"][subAdr]
            s = ",%3.1f,%d,"%(self.ps["tMotTotal"], self.ps["nMotLimit"] )
            #print("s=",s)
            self.txCmd = mb.wrap_modbus( modAdr, 0x25, subAdr, s )
            #print(txCmd)
            #print(txCmd)
            if self.net_dialog(self.txCmd) :
                return True
            return False

    def set_factory_settings(self,modAdr):
        if (self.blockStatus()): return 8 # blocked
        self.block()
        self.txCmd = mb.wrap_modbus( modAdr, 0x30, 0, "" )
        print(self.txCmd)
        if self.net_dialog(self.txCmd):
            return True
        return False


    def set_regulator_active(self, modAdr, subAdr, onOff ):
        if (self.blockStatus()): return 8 # blocked
        self.block()
        # onOff     0: switch off,  1: switch on
        if onOff != 0:
            onOff = 1
        s = ",%d,"%( onOff )
        self.txCmd = mb.wrap_modbus( modAdr, 0x35, subAdr, s )
        if self.net_dialog(self.txCmd):
            return True
        return False


        
    def valve_move(self, modAdr, subAdr, duration, direct):
        if (self.blockStatus()): return 8 # blocked
        self.block()
        # duration      ms;    motor-on time
        # dir           1;     0:close, 1:open, 2:startpos
        if subAdr in [1,2,3]:
            s = ",%d,%d,"%(duration,direct)
            self.txCmd = mb.wrap_modbus( modAdr, 0x31, subAdr, s )
            if self.net_dialog(self.txCmd):
                return True
            return False


    def set_normal_operation(self, modAdr):
        if (self.blockStatus()): return 8 # blocked
        self.block()
        self.txCmd = mb.wrap_modbus( modAdr, 0x34, 0, "" )
        if self.net_dialog(self.txCmd):
            return True
        return False


    def set_fast_mode(self, modAdr, mode ):
        if (self.blockStatus()): return 8 # blocked
        # onOff     0: normal mode,  else: fast operation
        self.block()
        s = ",%d,"%( mode )
        self.txCmd = mb.wrap_modbus( modAdr, 0x36, 0, s )
        if self.net_dialog(self.txCmd):
            return True
        return False


    def get_milisec(self, modAdr):
        if (self.blockStatus()): return 8 # blocked
        self.block()
        self.txCmd = mb.wrap_modbus( modAdr, 0x37, 0, "" )
        if self.net_dialog(self.txCmd):
            return True
        return False


    def cpy_eep2ram(self, modAdr):
        if (self.blockStatus()): return 8 # blocked
        self.block()
        self.txCmd = mb.wrap_modbus( modAdr, 0x38, 0, "" )
        if self.net_dialog(self.txCmd):
            return True
        return False

    def cpy_ram2eep(self, modAdr):
        if (self.blockStatus()): return 8 # blocked
        self.block()
        self.txCmd = mb.wrap_modbus( modAdr, 0x39, 0, "" )
        if self.net_dialog(self.txCmd):
            return True
        return False

    def wd_halt_reset(self, modAdr):
        if (self.blockStatus()): return 8 # blocked
        self.block()
        self.txCmd = mb.wrap_modbus( modAdr, 0x3A, 0, "" )
        if self.net_dialog(self.txCmd):
            return True
        return False

    def clr_eep(self ,modAdr):
        if (self.blockStatus()): return 8 # blocked
        self.block()
        self.txCmd = mb.wrap_modbus( modAdr, 0x3B, 0, "" )
        if self.net_dialog(self.txCmd):
            return True
        return False

    def check_motor(self, modAdr,subAdr):
        if (self.blockStatus()): return 8 # blocked
        self.block()
        self.txCmd = mb.wrap_modbus( modAdr, 0x3C, subAdr, "" )
        print("check_motor, txCmd=",self.txCmd)
        if self.net_dialog(self.txCmd):
            return True
        return False

    def calib_valve(self, modAdr,subAdr):
        if (self.blockStatus()): return 8 # blocked
        self.block()
        self.txCmd = mb.wrap_modbus( modAdr, 0x3D, subAdr, "" )
        if self.net_dialog(self.txCmd):
            return True
        return False

    def motor_off(self, modAdr,subAdr):
        if (self.blockStatus()): return 8 # blocked
        self.block()
        self.txCmd = mb.wrap_modbus( modAdr, 0x3E, subAdr, "" )
        if self.net_dialog(self.txCmd):
            return True
        return False

    def get_motor_current(self, modAdr):
        if (self.blockStatus()): return 8 # blocked
        self.block()
        self.txCmd = mb.wrap_modbus( modAdr, 0x3F, 0, "" )
        if self.net_dialog(self.txCmd):
            return True
        return False

    def lcd_backlight(self, modAdr, onOff):
        if (self.blockStatus()): return 8 # blocked
        self.block()
        if onOff:
            s=",1,"
        else:
            s=",0,"
        self.txCmd = mb.wrap_modbus( modAdr, 0x40, 0, s )
        if self.net_dialog(self.txCmd):
            return True
        return False

    def get_jumpers(self, modAdr):
        if (self.blockStatus()): return 8 # blocked
        self.block()
        self.txCmd = mb.wrap_modbus( modAdr, 0x41, 0, "" )
        if self.net_dialog(self.txCmd):
            return True
        return False


    # ---------------------------------------
    # interface for logger
    # ---------------------------------------

    import time


    def get_log_data(self, mod, reg, heizkreis):
        if (self.blockStatus()): return 8 # blocked
        # *** read status if module available
        x,y = self.ping(mod)
        if not x:
            print("module not available")
            return False
        else:

            self.read_stat(mod,reg)     # result is in cn2 and cn4
            #if (type(self.cn2))
            #self.get_milisec(mod)
            #self.get_jumpers(mod)

            # *** print data
            print("="*40)
            print("cn2=",self.cn2)
            print("cn4=",self.cn4)
            print("timestamp ms=",st.rxMillis)
            print("Jumper settings=%02x"%(st.jumpers))
            print("-"*40)
            
            # *** build a data-set
            # "20191016_075932 0401 HK2 :0002041a t4260659.0  S "
            # "VM 49.5 RM 47.8 VE 20.0 RE 47.8 RS 32.0 P074 E0000 FX0 M2452 A143"
            
            # header:
            dateTime = time.strftime("%Y%m%d_%H%M%S",time.localtime())
            self.header   ="%s %02X%02X HK%d :"%(dateTime,mod,reg,heizkreis)
            # module data:
            self.cmdHead  ="0002%02X%db "%(mod,reg)
            self.tic      = float(st.rxMillis) / 1000.0
            self.ticStr   ="t%.1f "%(self.tic)
            self.vlMeas   = float(self.cn2["VM"])
            self.rlMeas   = float(self.cn2["RM"])
            self.vlEff    = float(self.cn2["VE"])
            self.rlEff    = float(self.cn2["RE"])
            self.vlrl     = "VM%5.1f RM%5.1f VE%5.1f RE%5.1f "%(self.vlMeas,self.rlMeas,self.vlEff,self.rlEff)
            self.log_data_string = self.header + self.cmdHead + self.ticStr + self.cn2["SN"] + " " + self.vlrl

            '''
            %s VM%5.1f RM%5.1f VE%5.1f RE%5.1f RS%5.1f P%03d "\
                    "E%04X M%d A%d"%\
                    (st.rxMillis/1000.0, cn2["SN"], cn2["VM"], cn2["RM"], \
                        cn2["VE"], cn2["RE"], cn2["RS"], cn2["PM"], \
                        cn2["ER"], cn2["FX"], cn2["MT"], \
                        cn4[""], cn4[""] ) #nL NB ???
            '''
            print("LOGDATA:",self.log_data_string)
            return True


global ser_obj
ser_obj = Serbus()

if __name__ == "__main__":
    ser_obj.ser_check()
    ser_obj.get_log_data(4,1,2)






