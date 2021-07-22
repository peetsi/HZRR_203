#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#from __future__ import absolute_import

import copy
import gc
import inspect as it
import os
import platform
import threading as th
import time
import time as ti

import serial

import hr2_parse_answer as pan
import hr2_variables as hrv
import hz_rr_config as cg
import hz_rr_debug as dg
import hz_rr_log_n as lg
import modbus_b as mb
import vorlaut as vor
from hr2_variables import *


class Serbus(th.Thread):
    ser=port=baudrate=parity=stopbits=bytesize=timeout= \
    cmdHead=tic=ticStr=vlMeas=rlMeas=vlEff=rlEff=vlrl=dateTime=header= \
        cn2=cn4=txCmd=ps=p=read_stat_str=rxCmd=rxCmdLast=connected= None

    def __init__(self,serT=0.5,rxT=1,netR=3):
        self.threadID               = th.Thread.__init__(self)
        self.comm_req               = []
        self.comm_rsp               = ""
        self.comm_working           = False
        self.comm_rspTo             = ""
        self.comm_TTL               = 2 # seconds
        self.comm_getdone           = True # init value!
        self.comm_firstrun          = True
        self.logger_run             = 0
        self.menu_run               = 0
        self.dbg                    = dg.Debug(1)
        self.tries_last_ping        = 0
        self.logger_pause           = False
        self.terminal_running       = False
        self.block_log_until_TTL    = 0
        self._cn2                   = None
        self._cn4                   = None
        self.__rx_response          = None
        self.__rx_called_by_terminal= False
        self.serPortWin             = str(cg.conf_obj.r('system','serialPort_WIN' ))
        self.serPortPithr           = str(cg.conf_obj.r('system','serialPort_PIthree' ))
        self.serPortPifou           = str(cg.conf_obj.r('system','serialPort_PIfour' ))
        self.MAX_READ_STAT_RETRIES  = int(cg.conf_obj.r('SerialBus', 'max_read_stat_retry_count', 3))
        self.ser_bus_to             = float(cg.conf_obj.r('SerialBus','ser_bus_timeout', '-1' ))
        self.ser_bus_rx_to          = float(cg.conf_obj.r('SerialBus','ser_bus_rx_timeout', '-1' ))
        self.ser_bus_netdiag_max_try= int(cg.conf_obj.r('SerialBus','ser_bus_netdiag_max_try', '-1' ))
        self.ser_bus_baud_rate      = int(cg.conf_obj.r('SerialBus','ser_bus_baud_rate', '-1' ))
        self.SER_TIMEOUT            = serT   if self.ser_bus_to         == -1 else self.ser_bus_to
        self.RX_TIMEOUT             = rxT    if self.ser_bus_rx_to      == -1 else self.ser_bus_rx_to
        self.NET_REPEAT             = netR   if self.ser_bus_netdiag_max_try == -1 else self.ser_bus_netdiag_max_try
        self.baudrate               = 115200 if self.ser_bus_baud_rate  == -1 else self.ser_bus_baud_rate
        self.serPort                = self.serPortWin if not cg.conf_obj.islinux() else self.serPortPifou

        if cg.conf_obj.islinux(): # get raspi model number
            retval          = os.system('cat /proc/device-tree/model')#('cat /sys/firmware/devicetree/base/model')
            print(retval)
        super().setDaemon(True)
        super().start()
        self.dbg.m("Serbus communication handler succesfully initiated and thread started.")

    def run(self):
        once = 0
        while True:
            # work on the list
            if not self.comm_firstrun == True:
                while (not self.__work_available()):
                    pass #wait until work is available
                while (not self.__is_response_gathered()):
                    pass #wait until response is gathered.
            else:
                self.dbg.m("skipping the blockade on the first run. to avoid wrong debug messages.")

            if (self.comm_working == False):
                self.dbg.m("comm handle request start. waiting for request.")
                self.comm_handle_requests()
                once = 0
            else:
                if once == 0:
                    self.dbg.m("waiting for response to be gathered. TTL:", self.comm_TTL,"seconds")
                    once = 1
                # wait until response has been gathered
                pass


    def request(self, request_tuple, cbt=0):
        self.dbg.m("adding request:",request_tuple,cdb=2)
        self.__addRequest(request_tuple)

    def get_response(self,calling_thread_var=""): # just a check variable that not the wrong thread does steal the information
        # this identifies the calling thread and gives the 
        self.dbg.m("get_response():",calling_thread_var,cdb=3)
        retval = self.comm_rspTo

        if not self.__has_result():
            self.dbg.m("no result, retval:",retval)
            #self.__set_rx_response((False,""))
            return (False,"")

        if (calling_thread_var == retval): # this answer goes to the correct queue
            retval = self.comm_rsp
            #self.__set_rx_response((True,retval))
            self.__response_gathered()
            return (True,retval) # return response to asking thread

        else:
            self.dbg.m("sorry but the wrong queue has requested an answer. please wait (",calling_thread_var,"!=",self.comm_rspTo,cdb=2)
            #self.__set_rx_response((False,""))
            return (False,"")

    def response_available(self,for_who=""):
        #add TTL check
        self.dbg.m("checking for available response (response string:%s)"%(str(self.comm_rsp)),cdb=11)
        if (not self.__is_working()):
            self.dbg.m("__is_working(): False",cdb=15)
            if (not self.__response_empty()):
                self.dbg.m("__response_empty(): False",cdb=15)
                if (for_who == self.comm_rspTo):
                    return True
                else:
                    self.dbg.m("queue in use by:",self.comm_rspTo,"; usage tried by:",for_who,cdb=2)
            else:
                self.dbg.m("response is empty:",self.comm_rsp,cdb=2)
        return False

    def comm_handle_requests(self):
        self.comm_firstrun = False
        list_size =  len(self.comm_req)
        self.dbg.m("list size:",list_size,cdb=2)

        if list_size > 0: # there is work
            try:
                self.comm_working = True
                cmd = self.comm_req.pop(0) # get current work in the list
                #if len(cmd) > 3:
                #    if type(cmd[1]) != type(int()) or type(float()):
                #        self.dbg.m("type(cmd[1]) != type(int()):",(type(cmd[1]) != type(int())),cdb=9)
                #        return self.__setResponse((False,cmd[-1])) # any other error - false
                #    if type(cmd[2]) != type(int()) or type(float()):
                #        self.dbg.m("type(cmd[2]) != type(int()):",(type(cmd[1]) != type(int())),cdb=9)
                #        return self.__setResponse((False,cmd[-1])) # any other error - false

                # tuple style: (function_call, args, return_to)
                self.dbg.m("command and args found: ",cmd,cdb=2)
                self.dbg.m("command:",cmd[0],cdb=9)
                self.dbg.m("args:",cmd[1:len(cmd)-1],cdb=9)
                self.dbg.m("identifier:",cmd[-1],cdb=9)
                #func = "self."+cmd[0]+"("+cmd[1]+","
                #response = eval(func)

                if cmd[0] == "read_stat":
                    retval = self.read_stat(cmd[1],cmd[2])
                    self.dbg.m("read_stat retval:",retval,cdb=9)

                    if retval == False:
                        self.dbg.m("error retrieving cn2+4",cdb=9)
                        return self.__setResponse((False,cmd[-1]))

                    else:
                        if cmd[-1] == "ret_log_q":
                            lg.log_obj.cn2      = copy.deepcopy(self._cn2)
                            lg.log_obj.cn4      = copy.deepcopy(self._cn4)
                            lg.log_obj.jumpers  = st.jumpers
                            lg.log_obj.rxMillis = st.rxMillis
                            prnt = "cn2=%s;cn4=%s;jumpers=%s;rxMillis=%s"%(str(lg.log_obj.cn2),str(lg.log_obj.cn4),str(lg.log_obj.jumpers),str(lg.log_obj.rxMillis))
                            self.dbg.m("success. data:",prnt,cdb=9)

                        elif cmd[-1] == "ret_mon_q":
                            hrv.cn2      = copy.deepcopy(self._cn2)
                            hrv.cn4      = copy.deepcopy(self._cn4)
                            hrv.jumpers  = st.jumpers
                            hrv.rxMillis = st.rxMillis
                            prnt = "cn2=%s;cn4=%s;jumpers=%s;rxMillis=%s"%(str(hrv.cn2),str(hrv.cn4),str(hrv.jumpers),str(hrv.rxMillis))
                            self.dbg.m("success. data:",prnt,cdb=9)

                        elif cmd[-1] == "TERMINAL":
                            hrv.cn2      = copy.deepcopy(self._cn2)
                            hrv.cn4      = copy.deepcopy(self._cn4)
                            hrv.jumpers  = st.jumpers
                            hrv.rxMillis = st.rxMillis
                            prnt = "cn2=%s;cn4=%s;jumpers=%s;rxMillis=%s"%(str(hrv.cn2),str(hrv.cn4),str(hrv.jumpers),str(hrv.rxMillis))
                            self.dbg.m("success. data:",prnt,cdb=9)

                        elif cmd[-1] == "ret_mon_valve_failback":
                            hrv.cn2      = copy.deepcopy(self._cn2)
                            hrv.cn4      = copy.deepcopy(self._cn4)
                            hrv.jumpers  = st.jumpers
                            hrv.rxMillis = st.rxMillis
                            prnt = "cn2=%s;cn4=%s;jumpers=%s;rxMillis=%s"%(str(hrv.cn2),str(hrv.cn4),str(hrv.jumpers),str(hrv.rxMillis))
                            self.dbg.m("success. data:",prnt,cdb=9)


                        return self.__setResponse((self.read_stat_str,cmd[-1]))# it did work.

                elif cmd[0] == "ping":
                    answer, repeat = self.ping(int(cmd[1]))
                    self.dbg.m("ping answer:",answer,cdb=9)
                    return self.__setResponse((answer,cmd[-1])) # gives back false or true

                elif cmd[0] == "get_jumpers":
                    answer = self.get_jumpers(int(cmd[1]))
                    self.dbg.m("get_jumpers answer:",st.jumpers,cdb=9)
                    return self.__setResponse((st.jumpers,cmd[-1])) # gives back false or true

                elif cmd[0] == "get_millis":
                    answer = self.get_millis(int(cmd[1]))
                    self.dbg.m("get_millis answer:",st.rxMillis,cdb=9)
                    return self.__setResponse((st.rxMillis,cmd[-1])) # gives back millis

                elif cmd[0] == "get_param":
                    answer = self.get_param(int(cmd[1]),int(cmd[2]))
                    self.dbg.m("get_param answer:",answer,cdb=9)
                    return self.__setResponse((answer,cmd[-1])) # gives back false or true

                elif cmd[0] == "send_tvor":
                    answer = self.send_Tvor(int(cmd[1]),float(cmd[2]))
                    self.dbg.m("send_Tvor answer:",answer,cdb=9)
                    return self.__setResponse((answer,cmd[-1])) # gives back false or true

                elif cmd[0] == "send_param":
                    answer = self.send_param(int(cmd[1]),int(cmd[2]))
                    self.dbg.m("send_param answer:",answer,cdb=9)
                    return self.__setResponse((answer,cmd[-1])) # gives back false or true

                elif cmd[0] == "set_motor_lifetime_status":
                    answer = self.set_motor_lifetime_status(int(cmd[1]),int(cmd[2]))
                    self.dbg.m("set_motor_lifetime_status answer:",answer,cdb=9)
                    return self.__setResponse((answer,cmd[-1])) # gives back false or true

                elif cmd[0] == "set_factory_settings":
                    answer = self.set_factory_settings(int(cmd[1]))
                    self.dbg.m("set_fatory_settings answer:",answer,cdb=9)
                    return self.__setResponse((answer,cmd[-1])) # gives back false or true

                elif cmd[0] == "valve_move":
                    answer = self.valve_move(int(cmd[1]),int(cmd[2]),int(cmd[3]),int(cmd[4]))
                    self.dbg.m("valve_move answer:",answer,cdb=9)
                    return self.__setResponse((answer,cmd[-1])) # gives back false or true

                elif cmd[0] == "set_regulator_active":
                    answer = self.set_regulator_active(int(cmd[1]),int(cmd[2]),int(cmd[3]))
                    self.dbg.m("set_regulator_active answer:",answer,cdb=9)
                    return self.__setResponse((answer,cmd[-1])) # gives back false or true

                elif cmd[0] == "set_fast_mode":
                    answer = self.set_fast_mode(int(cmd[1]),int(cmd[2]))
                    self.dbg.m("set_fast_mode answer:",answer,cdb=9)
                    return self.__setResponse((answer,cmd[-1])) # gives back false or true

                elif cmd[0] == "cpy_eep2ram":
                    answer = self.cpy_eep2ram(int(cmd[1]))
                    self.dbg.m("cpy_eep2ram answer:",answer,cdb=9)
                    return self.__setResponse((answer,cmd[-1])) # gives back false or true

                elif cmd[0] == "cpy_ram2eep":
                    answer = self.cpy_ram2eep(int(cmd[1]))
                    self.dbg.m("cpy_ram2eep answer:",answer,cdb=9)
                    return self.__setResponse((answer,cmd[-1])) # gives back false or true

                elif cmd[0] == "wd_halt_reset":
                    answer = self.wd_halt_reset(int(cmd[1]))
                    self.dbg.m("wd_halt_reset answer:",answer,cdb=9)
                    return self.__setResponse((answer,cmd[-1])) # gives back false or true

                elif cmd[0] == "clr_eep":
                    answer = self.clr_eep(int(cmd[1]))
                    self.dbg.m("clr_eep answer:",answer,cdb=9)
                    return self.__setResponse((answer,cmd[-1])) # gives back false or true

                elif cmd[0] == "check_motor":
                    answer = self.check_motor(int(cmd[1]),int(cmd[2]))
                    self.dbg.m("check_motor answer:",answer,cdb=9)
                    return self.__setResponse((answer,cmd[-1])) # gives back false or true

                elif cmd[0] == "calib_valve":
                    answer = self.calib_valve(int(cmd[1]),int(cmd[2]))
                    self.dbg.m("calib_valve answer:",answer,cdb=9)
                    return self.__setResponse((answer,cmd[-1])) # gives back false or true

                elif cmd[0] == "motor_off":
                    answer = self.motor_off(int(cmd[1]),int(cmd[2]))
                    self.dbg.m("motor_off answer:",answer,cdb=9)
                    return self.__setResponse((answer,cmd[-1])) # gives back false or true

                elif cmd[0] == "get_motor_current":
                    answer = self.get_motor_current(int(cmd[1]))
                    self.dbg.m("get_motor_current answer:",answer,cdb=9)
                    return self.__setResponse((answer,cmd[-1])) # gives back false or true

                elif cmd[0] == "lcd_backlight":
                    answer = self.lcd_backlight(int(cmd[1]),int(cmd[2]))
                    self.dbg.m("lcd_backlight answer:",answer,cdb=9)
                    return self.__setResponse((answer,cmd[-1])) # gives back false or true

                elif cmd[0] == "get_param":
                    answer = self.get_param(int(cmd[1]),int(cmd[2]))
                    self.dbg.m("get_param answer:",answer,cdb=9)
                    return self.__setResponse((answer,cmd[-1])) # gives back false or true

                elif cmd[0] == "send_param":
                    answer = self.send_param(int(cmd[1]),int(cmd[2]))
                    self.dbg.m("send_param answer:",answer,cdb=9)
                    return self.__setResponse((answer,cmd[-1])) # gives back false or true

                elif cmd[0] == "set_normal_operation":
                    answer = self.set_normal_operation(int(cmd[1]))
                    self.dbg.m("set_normal_operation answer:",answer,cdb=9)
                    return self.__setResponse((answer,cmd[-1])) # gives back false or true

                elif cmd[0] == "change_param": #(change_param,r,reg,name,val)
                    #temp =
                    self.dbg.m("change_param before:",parameter[str(cmd[1])][int(cmd[2])][str(cmd[3])],cdb=9)
                    parameter[str(cmd[1])][int(cmd[2])][str(cmd[3])] = float(cmd[4])
                    self.dbg.m("change_param after:",parameter[str(cmd[1])][int(cmd[2])][str(cmd[3])],cdb=9)
                    return self.__setResponse((parameter[str(cmd[1])][int(cmd[2])][str(cmd[3])],cmd[-1])) # gives back false or true

                elif cmd[0] == "show_param":
                    #show_param,parameters,1-30
                    if len(cmd) <= 2: return self.__setResponse((eval(cmd[1]),cmd[-1]))
                    args =  tuple(map(str, cmd[1:-1])) #tuple(map(str, v.replace(' ','').split(',')))
                    self.dbg.m("show_param:",args,cdb=9)
                    # parameter # parameters # par # pa # st
                    t = "[%s]"
                    hs = t
                    for x in args:
                        hs += t%(x)
                    print(hs)
                    a= args[0]
                    value = eval( a ) #+hs )
                    #print(parameter)
                    return self.__setResponse((value,cmd[-1]))

                elif cmd[0] == "set_param":
                    #set_param,parameters,1-30
                    if len(cmd) <= 2: return self.__setResponse((eval(cmd[1]),cmd[-1]))
                    args =  tuple(map(str, cmd[1:-1])) #tuple(map(str, v.replace(' ','').split(',')))
                    self.dbg.m("show_param:",args,cdb=9)
                    # parameter # parameters # par # pa # st
                    t = "[%s]"
                    hs = t
                    for x in args:
                        hs += t%(x)
                    print(hs)   # args[0], args[1], args[2]
                    a= args[0]  #parameter,tr0,wert
                                #parameter[rt0] = 44

                    m = args[1]
                    e = args[2]
                    exec( a+ "['"+m+"'] = "+e)
                    _str = a+ "['"+m+"']"
                    time.sleep(0.01)
                    value = eval( _str ) #+hs )
                    print(parameter)
                    return self.__setResponse((value,cmd[-1]))

                elif cmd[0] == "exec":
                    #set_param,parameters,1-30
                    if len(cmd) <= 2:
                        self.dbg.m("exec command too little params:",cmd,cdb=9)
                        return self.__setResponse((False,cmd[-1])) # exec command to short
                    args =  tuple(map(str, cmd[1:-1])) #tuple(map(str, v.replace(' ','').split(',')))
                    self.dbg.m("show_param:",args,cdb=9)
                    # parameter # parameters # par # pa # st
                    t = "[%s]"
                    hs = t
                    for x in args:
                        hs += t%(x)
                    print(hs)   # args[0], args[1], args[2]
                    a= args[0]  #parameter,tr0,wert
                                #parameter[rt0] = 44

                    m = args[1]
                    e = args[2]
                    exec( a+ "['"+m+"'] = "+e)
                    _str = a+ "['"+m+"']"
                    time.sleep(0.01)
                    value = eval( _str ) #+hs )
                    print(parameter)
                    return self.__setResponse((value,cmd[-1]))

                else:
                    self.dbg.m("fail:",cmd,cdb=9)
                    return self.__setResponse((False,cmd[-1])) # any other error - false

            finally:
                self.comm_working = False
                self.comm_getdone = False
        pass

    # internal functions - DONT CALL MANUALLY!

    # RX receiver functions
    def get_rx_response(self):
        x = self.__rx_response
        if x != None:
            self.dbg.m("__get_rx_response:",x,cdb=3)
            self.__reset_rx_response()
            return x
        else:
            self.__reset_rx_response()
            self.dbg.m("__get_rx_response: 'None' (empty)", cdb=3)
            return ""

    def __append_tx_response(self,val,cbt=False):
        if cbt == False:
            return self.dbg.m("__append_tx_response: not called by terminal",cdb=3)
        if self.__rx_response == None: self.__rx_response = ""
        self.__rx_response += "\n" + str(val)
        self.dbg.m("__append_tx_response:",self.__rx_response,cdb=3)

    def __set_rx_response(self,val):
        self.__append_tx_response( str(val), self.__rx_called_by_terminal )
        #x = self.__rx_respose
        #if x != "":
        #else:
        #    self.dbg.m("__set_rx_response: self.__rx_response not empty(%s)"%(x),cdb=3)

    def set_called_by_terminal(self,v=True):
        if v == True:
            self.__set_called_by_terminal(True)
        else:
            self.__set_called_by_terminal(False)

    def __set_called_by_terminal(self, v=True):
        self.__rx_called_by_terminal = True
        pan.pa_to_ser_obj.from_term(True)


    def __reset_rx_response(self):
        self.__rx_called_by_terminal = False
        self.__rx_response = None

    #INTERNAL QUERXY HANDLER functions
    def __response_empty(self):
        self.dbg.m("__response_empty():", (True if self.comm_rsp == "" else False), cdb=9)
        return True if self.comm_rsp == "" else False

    def __work_available(self):
        self.dbg.m("is work available:", (True if len(self.comm_req)>0 else False), cdb=11)
        return True if len(self.comm_req) > 0 else False

    def __is_working(self):
        self.dbg.m("is working:",self.comm_working,cdb=11)
        return self.comm_working

    def __has_result(self):
        self.dbg.m("__has_result()",cdb=9)
        if not self.__is_working():
            self.dbg.m("__is_working():",     self.__is_working(),    cdb=15)
            if not self.__response_empty():
                return True
        return False

    def __addRequest(self,request_tuple):
        self.dbg.m("adding request:",request_tuple,cdb=9)
        #gc.disable()
        return self.comm_req.append(request_tuple)
        #gc.enable()

    def __setResponse(self,response):
        x = response
        self.dbg.m("RESPONSE: (comm_rsp=%s; comm_rspTo=%s; comm_working=%s; comm_getdone=%s)"%(x[0],x[1],0,False),cdb=3)
        self.comm_rsp       = x[0]
        self.comm_rspTo     = x[-1]
        self.__set_rx_response( '%s -> %s'%(str(self.comm_rsp),str(self.comm_rspTo)) )
        self.comm_working   = False
        self.comm_getdone   = False

    def __response_gathered(self):
        self.dbg.m("__response_gathered():",self.comm_rspTo,cdb=9)
        self.comm_rsp       = ""
        self.comm_rspTo     = ""
        self.comm_working   = False
        self.comm_getdone   = True
        self.comm_firstrun  = False

    def __is_response_gathered(self): # combine with TTL check
        if self.comm_firstrun == True: return False
        self.dbg.m("__is_response_gathered():",self.comm_getdone,", firstrun:",self.comm_firstrun,cdb=9)
        return self.comm_getdone

    def ser_instant(self) :
        self.dbg.m("try: opening serial connectio: { port:",self.serPort,", baudrate:",self.baudrate, \
                    ", parity:", serial.PARITY_NONE, ", stopbits:", serial.STOPBITS_TWO, \
                        ", bytesize:", serial.EIGHTBITS, ", timeout:", self.SER_TIMEOUT,"}",cdb=1)
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
        return err

    def ser_open(self):
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
        return err

    def ser_reset_buffer(self):
        err=0
        try:
            self.ser.flushOutput()  # newer: ser.reset_output_buffer()
            self.ser.flushInput()   # newer: ser.reset_input_buffer()
        except serial.SerialException as e:
            err = 5
            vor.vorlaut( 3,  "05 cannot erase serial buffers")
            vor.vorlaut( 3,  "   exception = %s"%(e))
        except Exception as e:
            err = 6
            vor.vorlaut( 3,  "06 something else is wrong with serial port: %s"%(self.serPort))
            vor.vorlaut( 3,  "   exception = %s"%(e))
        return err

    def ser_check(self):
        self.ser_instant()
        if self.ser.isOpen() == False :
            self.connected=0
            self.dbg.m("open network",cdb=1)
            err = 0
            err |= self.ser_open()
            if( err ) :
                self.dbg.m("rs485 Netz: %d"%(err),cdb=1)
            time.sleep(1.0)
            self.ser_reset_buffer()
        self.dbg.m("rs485 Netz verbunden",cdb=1)
        self.connected=1
        return

    def txrx_command(self, txCmd) :
        self.ser.reset_output_buffer()
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
        self.ser.reset_input_buffer()  # newer:
        st.rxCmd = ""
        self.rxCmdLast=self.rxCmd
        self.rxCmd=""

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
        return line

    def net_dialog(self, txCmd, info=0 ):
        self.txCmd = txCmd
        maxCnt = self.NET_REPEAT
        repeat = 0
        self.tries_last_ping = repeat
        #ready  = False
        while repeat < maxCnt :
            self.dbg.m("resetting buffer",cdb=9)
            self.ser_reset_buffer()
            self.dbg.m("sending:",txCmd.replace('\n',''), cdb=2)
            self.txrx_command( txCmd )
            self.dbg.m("parsing answer.. entering pan.parse_answer():",cdb=9)
            #self.dbg.m(pan.parse_answer(),cdb=9)
            pan.pa_to_ser_obj.from_term(self.__rx_called_by_terminal)
            parse = pan.parse_answer()
            self.__set_rx_response(pan.pa_to_ser_obj.get())
            pan.pa_to_ser_obj.from_term(False)
            self.dbg.m("parse_answer return:",parse,cdb=9)
            if parse:
                if info==0:
                    return True#, repeat
                return True, repeat
            else:
                repeat += 1
                self.tries_last_ping = repeat
                self.dbg.m("pan.parse_answer() ELSE occured! - did txcmd change:",txCmd,"//",self.txCmd,cdb=9)
        if info==0:
            return False#, repeat
        return False, repeat

    # *****************************************
    # *** module communication commands     ***
    # *****************************************

    def ping(self, modAdr ):
        self.txCmd = mb.wrap_modbus( modAdr, 1, 0, "" )   # cmd==1: send ping
        x, y = self.net_dialog(self.txCmd, 1)
        #self.__set_rx_response('txCmd:   %s'%(str(self.txCmd)))
        #self.__set_rx_response('ping x:  %s'%(str(x)))
        #self.__set_rx_response('ping y:  %s'%(str(y)))
        return x, y

    def read_stat(self, modAdr, subAdr):#, retry_count=0, skip_first=0 ) :
        ''' read all status values from module
            using command 2 and 4
        '''
        self.__set_rx_response('read_stat(mod=%s,sub=%s)'%(str(modAdr),str(subAdr)))

        self.txCmd = mb.wrap_modbus( modAdr, 2, subAdr, "" )
        if not self.net_dialog(self.txCmd):
            return False
        self._cn2      = copy.deepcopy(cn2)
        #self.__set_rx_response('cn2: %s'%(str(cn2)))
        time.sleep(0.01)#0.25)

        self.txCmd = mb.wrap_modbus( modAdr, 4, subAdr, "" )
        if not self.net_dialog(self.txCmd):
            return False
        self._cn4      = copy.deepcopy(cn4)
        #self.__set_rx_response('cn4: %s'%(str(cn4)))


        f=2#self.dbg.const( "__DBG_LVL_FUNCTIONS_AND_RETURN" )
        self.get_milisec(modAdr)
        self.dbg.m("get_milisec():",st.rxMillis,cdb=f)
        self.get_jumpers(modAdr)
        self.dbg.m("get_jumpers():",st.jumpers,cdb=f)
        # module data:
        self.cmdHead  = "0002%02X%db "%(int(modAdr),int(subAdr))
        self.tic      = float(st.rxMillis) / 1000.0
        self.ticStr   = "t%.1f "%(self.tic)

        #cn2={"SN":0,"VM":0,"RM":0,"VE":0,"RE":0,"RS":0,"PM":0}
        self.vlMeas   = float(self._cn2["VM"])
        self.rlMeas   = float(self._cn2["RM"])
        self.vlEff    = float(self._cn2["VE"])
        self.rlEff    = float(self._cn2["RE"])
        self.rlSoll   = float(self._cn2["RS"])
        self.posMot   = float(self._cn2["PM"])

        #cn4={"ER":0,"FX":0,"MT":0,"NL":0} # command names
        self.erFlag  = int(self._cn4["ER"])
        self.fixPos  = float(self._cn4["FX"])
        self.motTime = float(self._cn4["MT"])
        self.nLimit  = int(self._cn4["NL"])

        s1    = "VM%5.1f RM%5.1f VE%5.1f RE%5.1f "%(self.vlMeas,self.rlMeas,self.vlEff,self.rlEff)
        s2    = "RS%5.1f P%03.0f "%(self.rlSoll, self.posMot)
        s3    = "E%04X FX%.0f M%.0f A%d"%(self.erFlag,self.fixPos,self.motTime,self.nLimit)
        # FX muss noch übersetzt werden.
        x = s1 + s2 + s3
        self.read_stat_str = str(self.cmdHead) + str(self.ticStr) + str(self._cn2["SN"]) + " " + str(x)
        self.dbg.m("read_stat_str: ", self.read_stat_str, cdb=9)
        return self.read_stat_str

    def get_param(self, modAdr,subAdr):
        modAdr = int(modAdr)
        subAdr = int(subAdr)
        '''read module-related parameter set from module'''
        if subAdr in [0,1,2,3]:
            self.txCmd = mb.wrap_modbus( modAdr, 0x05, subAdr,"" )
            if not  self.net_dialog(self.txCmd):
                return False
            elif subAdr == 0:
                return True

            self.txCmd = mb.wrap_modbus( modAdr, 0x06, subAdr,"" )
            if not  self.net_dialog(self.txCmd):
                return False

            self.txCmd = mb.wrap_modbus( modAdr, 0x07, subAdr,"" )
            if self.net_dialog(self.txCmd):
                return True

    def send_Tvor(self, modAdr,tempSend):
        '''send Vorlauftemperatur to module'''
        self.txCmd = mb.wrap_modbus(modAdr,0x20,0,','+"%.1f"%(float(tempSend))+',')
        if self.net_dialog(self.txCmd):
            return True
        return False

    def send_param(self, modAdr,subAdr):
        try:
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
                s = ",%03d,%03d,%02d,%4.1f,%4.1f,%4.1f,%4.1f,%02d,%02d,%4.1f,%3.1f,"%( \
                    self.p["timer1Tic"], self.p["tMeas"], self.p["dtBackLight"], self.p["tv0"], \
                    self.p["tv1"], self.p["tr0"], self.p["tr1"], self.p["tVlRxValid"], self.p["tVlRxValid"], \
                    self.p["tempZiSoll"], self.p["tempZiTol"] )
                #print("s=",s)
                self.txCmd = mb.wrap_modbus( modAdr, 0x22, subAdr, s )
                #self.txCmd = mb.wrap_modbus( modAdr, 0x22, subAdr, "" )
                #print(txCmd)
                if self.net_dialog(self.txCmd):
                    return True
                return False

            elif subAdr in [1,2,3]: # parameter regulator, part 1,2,3
                # send:
                #   active, motIMin, motIMax, tMotDelay, tMotMin, tMotMax,
                #   dtOpen, dtClose, dtOffset
                #time.sleep(0.2)
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
                #time.sleep(0.2)
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
        finally:
            pass


    def set_motor_lifetime_status(self,modAdr,subAdr):
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
        self.txCmd = mb.wrap_modbus( modAdr, 0x30, 0, "" )
        self.dbg.m(self.txCmd,cdb=1)
        if self.net_dialog(self.txCmd):
            return True
        return False


    def set_regulator_active(self, modAdr, subAdr, onOff ):
        # onOff     0: switch off,  1: switch on
        if onOff != 0:
            onOff = 1
        s = ",%d,"%( onOff )
        self.txCmd = mb.wrap_modbus( modAdr, 0x35, subAdr, s )
        if self.net_dialog(self.txCmd):
            return True
        return False



    def valve_move(self, modAdr, subAdr, duration, direct):
        # duration      ms;    motor-on time
        # dir           1;     0:close, 1:open, 2:startpos
        if subAdr in [1,2,3]:
            s = ",%d,%d,"%(duration,direct)
            self.txCmd = mb.wrap_modbus( modAdr, 0x31, subAdr, s )
            if self.net_dialog(self.txCmd):
                return True
            return False


    def set_normal_operation(self, modAdr):
        self.txCmd = mb.wrap_modbus( modAdr, 0x34, 0, "" )
        if self.net_dialog(self.txCmd):
            return True
        return False


    def set_fast_mode(self, modAdr, mode ):
        # onOff     0: normal mode,  else: fast operation
        s = ",%d,"%( mode )
        self.txCmd = mb.wrap_modbus( modAdr, 0x36, 0, s )
        if self.net_dialog(self.txCmd):
            return True
        return False


    def get_milisec(self, modAdr):
        try:
            self.txCmd = mb.wrap_modbus( modAdr, 0x37, 0, "" )
            if self.net_dialog(self.txCmd):
                return True
            return False
        finally:
            pass


    def cpy_eep2ram(self, modAdr):
        try:
            self.txCmd = mb.wrap_modbus( modAdr, 0x38, 0, "" )
            if self.net_dialog(self.txCmd):
                return True
            return False
        finally:
            pass

    def cpy_ram2eep(self, modAdr):
        try:
            self.txCmd = mb.wrap_modbus( modAdr, 0x39, 0, "" )
            if self.net_dialog(self.txCmd):
                return True
            return False
        finally:
            pass

    def wd_halt_reset(self, modAdr):
        try:
            self.txCmd = mb.wrap_modbus( modAdr, 0x3A, 0, "" )
            if self.net_dialog(self.txCmd):
                return True
            return False
        finally:
            pass

    def clr_eep(self ,modAdr):
        try:
            self.txCmd = mb.wrap_modbus( modAdr, 0x3B, 0, "" )
            if self.net_dialog(self.txCmd):
                return True
            return False
        finally:
            pass

    def check_motor(self, modAdr,subAdr):
        try:
            self.txCmd = mb.wrap_modbus( modAdr, 0x3C, subAdr, "" )
            self.dbg.m("check_motor, txCmd=",self.txCmd,cdb=1)
            if self.net_dialog(self.txCmd):
                return True
            return False
        finally:
            pass

    def calib_valve(self, modAdr,subAdr):
        try:
            self.txCmd = mb.wrap_modbus( modAdr, 0x3D, subAdr, "" )
            if self.net_dialog(self.txCmd):
                return True
            return False
        finally:
            pass

    def motor_off(self, modAdr,subAdr):
        try:
            self.txCmd = mb.wrap_modbus( modAdr, 0x3E, subAdr, "" )
            if self.net_dialog(self.txCmd):
                return True
            return False
        finally:
            pass

    def get_motor_current(self, modAdr):
        try:
            self.txCmd = mb.wrap_modbus( modAdr, 0x3F, 0, "" )
            if self.net_dialog(self.txCmd):
                return True
            return False
        finally:
            pass

    def lcd_backlight(self, modAdr, onOff):
        try:
            if onOff:
                s=",1,"
            else:
                s=",0,"
            self.txCmd = mb.wrap_modbus( modAdr, 0x40, 0, s )
            if self.net_dialog(self.txCmd):
                return True
            return False
        finally:
            pass

    def get_jumpers(self, modAdr):
        self.txCmd = mb.wrap_modbus( modAdr, 0x41, 0, "" )
        if self.net_dialog(self.txCmd):
            #self.__set_rx_response('get_jumpers:%s'%(st.jumpers))
            return True
        #self.__set_rx_response('get_jumpers:%s'%("fail"))
        return False

    def get_version(self, modAdr):
        # TODO: add function to later Arduino-Nano Firmware
        #       with own command-nr
        # not implemented in Arduino-Nano Version
        # 1.0.b, 2020-09-26, "hr2_reg07pl_Serie01/..."

        # version of modules which do not answer
        st.fwVersion = "1.0.b"
        st.fwDate = "2020-09-26"
        return True
    # ---------------------------------------
    # interface for logger
    # ---------------------------------------

    import time


    def get_log_data(self, mod, reg, heizkreis):
        # *** read status if module available
        x,y = self.ping(mod)
        if not x:
            self.dbg.m("module {%s} not available"%(mod),cdb=1)
            #return False
        else:

            self.read_stat(mod,reg)     # result is in cn2 and cn4
            #if (type(self.cn2))
            #self.get_milisec(mod)
            #self.get_jumpers(mod)

            # *** print data
            self.dbg.m("="*120,cdb=1)
            self.dbg.m("cn2=",str(self.cn2),cdb=1)
            self.dbg.m("cn4=",str(self.cn4),cdb=1)
            self.dbg.m("timestamp ms=",st.rxMillis,cdb=1)
            self.dbg.m("Jumper settings=%02x"%(st.jumpers),cdb=1)
            self.dbg.m("-"*120,cdb=1)

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
            self.log_data_string = self.header + self.cmdHead + self.ticStr + str(self.cn2["SN"]) + " " + self.vlrl
            self.log_data_string = self.read_stat_str
            '''
            %s VM%5.1f RM%5.1f VE%5.1f RE%5.1f RS%5.1f P%03d "\
                    "E%04X M%d A%d"%\
                    (st.rxMillis/1000.0, cn2["SN"], cn2["VM"], cn2["RM"], \
                        cn2["VE"], cn2["RE"], cn2["RS"], cn2["PM"], \
                        cn2["ER"], cn2["FX"], cn2["MT"], \
                        cn4[""], cn4[""] ) #nL NB ???
            '''
            self.dbg.m("LOGDATA:",self.log_data_string,cdb=1)
            #self.unblock()
            return True


global ser_obj
ser_obj = Serbus()
pa = pan.pa_to_ser_obj
#ser_obj.ser_check()


def ser_add_work( t = tuple, cbt=0 ):
    global ser_obj, pa
    if cbt == 1:
        ser_obj.set_called_by_terminal()
    #mydict = dict((y, x) for x, y in t) ("fucntion name",a,n,identifier)
    ser_obj.request(t)
    dbeg = dg.Debug(1)
    while not ser_obj.response_available(t[-1]):   # wait for answer            # in response_available has to be added a TTL value.
        pass
    r = ser_obj.get_response(t[-1])
    if r[0] == False:
        dbeg.m("error running:",str(t),cdb=2)
    ser_obj.__rx_called_by_terminal = False
    return r

    eval('self.'+key+'()')


if __name__ == "__main__":

    ser_obj.ser_check()
    dbeg = dg.Debug(1)

    x= "USBSERBUS_IDENTIFIER"
    modAdr = 4
    subAdr = 1

    y = ser_obj.request(("read_stat",modAdr,subAdr,x))
    while not ser_obj.response_available(x): 
        pass

    r = ser_obj.get_response(x)
    if not r[0] == False:
        dbeg.m("got cn2+cn4 -> deepcopy into log_obj.cn2/cn4.",cdb=2)
        dbeg.m("log_obj.cn2:", lg.log_obj.cn2,cdb=9) # 9 = verbose debug
        dbeg.m("log_obj.cn4:", lg.log_obj.cn4,cdb=9) # 9 = verbose debug

    else:
        dbeg.m("error getting cn2 and cn4",cdb=2)

    pass
