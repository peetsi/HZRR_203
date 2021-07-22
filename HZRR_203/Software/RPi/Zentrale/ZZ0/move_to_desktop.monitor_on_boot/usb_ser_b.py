#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#from __future__ import absolute_import

import copy
import functools
import gc
import inspect as it
import os
import platform
import random
import string
import threading as th
import time

import serial

import hr2_parse_answer as pan
import hr2_variables as hrv
import hz_rr_config as cg
import hz_rr_debug as dg
import hz_rr_log_n as lg
import modbus_b as mb
import vorlaut as vor
from hr2_variables import *
from hr2_variables import get_cn, get_cn_d


def singleton(cls):
    """Make a class a Singleton class (only one instance)"""
    @functools.wraps(cls)
    def wrapper_singleton(*args, **kwargs):
        if not wrapper_singleton.instance:
            wrapper_singleton.instance = cls(*args, **kwargs)
        return wrapper_singleton.instance
    wrapper_singleton.instance = None
    return wrapper_singleton

@singleton
class Serbus(th.Thread):
    ser=port=baudrate=parity=stopbits=bytesize=timeout= \
        cmdHead=tic=ticStr=vlMeas=rlMeas=vlEff=rlEff=vlrl=dateTime=header= \
            txCmd=ps=p=read_stat_str=rxCmd=rxCmdLast=connected= None

    def __init__(self,serT=0.5,rxT=1,netR=3):
        self.threadID                   = th.Thread.__init__(self)
        self.comm_req                   = []
        self.comm_rsp                   = ""
        self.comm_working               = False
        self.comm_rspTo                 = ""
        self.comm_rspListDict           = list()# [{'':''},]
        self.comm_ttl_count_dct         = dict()
        self.comm_ttl_count_max         = 7                 # retries before dumping the answer from the response queue
        self.comm_TTL                   = int(cg.conf_obj.r('SerialBus', 'queue_handler_max_ttl', 7)) # second maximum until queue force-ends
        self.comm_TTL_timer_end         = None
        self.comm_TTL_timer             = None
        self.comm_TTL_timer_s_end       = None
        self.comm_TTL_timer_s           = None
        self.comm_getdone               = True # init value!
        self.comm_firstrun              = True
        self.logger_pause               = False
        self.terminal_running           = False
        self.dbg                        = dg.Debug(1)
        self.tries_last_ping            = 0
        self.__rx_response              = None
        self.__rx_called_by_terminal    = False
        self.block_log_until_TTL        = 0
        self.logger_run                 = 0
        self.menu_run                   = 0
        self.serPortWin                 = str(cg.conf_obj.r('system','serialPort_WIN' ))
        self.serPortPithr               = str(cg.conf_obj.r('system','serialPort_PIthree' ))
        self.serPortPifou               = str(cg.conf_obj.r('system','serialPort_PIfour' ))
        self.MAX_READ_STAT_RETRIES      = int(cg.conf_obj.r('SerialBus', 'max_read_stat_retry_count', 3))
        self.ser_bus_to                 = float(cg.conf_obj.r('SerialBus','ser_bus_timeout', '-1' ))
        self.ser_bus_rx_to              = float(cg.conf_obj.r('SerialBus','ser_bus_rx_timeout', '-1' ))
        self.ser_bus_netdiag_max_try    = int(cg.conf_obj.r('SerialBus','ser_bus_netdiag_max_try', '-1' ))
        self.ser_bus_baud_rate          = int(cg.conf_obj.r('SerialBus','ser_bus_baud_rate', '-1' ))
        self.SER_TIMEOUT                = serT   if self.ser_bus_to         == -1 else self.ser_bus_to
        self.RX_TIMEOUT                 = rxT    if self.ser_bus_rx_to      == -1 else self.ser_bus_rx_to
        self.NET_REPEAT                 = netR   if self.ser_bus_netdiag_max_try == -1 else self.ser_bus_netdiag_max_try
        self.baudrate                   = 115200 if self.ser_bus_baud_rate  == -1 else self.ser_bus_baud_rate
        self.serPort                    = self.serPortWin if not cg.conf_obj._tbl.islinux() else self.serPortPifou
        self.queue_failsafe_counter     = 0
        self.queue_failsafe_counter_max = 6
        self.running                    = True
        self.spam_debug_level           = 11
        self._this_response_request_by  = ""

        if cg.conf_obj._tbl.islinux(): # get raspi model number
            retval          = os.system('cat /proc/device-tree/model')#('cat /sys/firmware/devicetree/base/model')
            print(retval)
        super().setDaemon(True)
        super().start()
        self.dbg.m("Serbus communication handler started", cdb = 1)

    def __del__(self):
        self.running = False

    def __call__(self):
        pass

    def run(self):
        while True:
            time.sleep(0.01)
            self.__comm_check_all_ttls()
            # work on the list
            if not self.comm_firstrun == True:
                while (not self.__work_available()):
                    pass #wait until work is available
                #while (not self.__is_response_gathered()):
                #    pass #wait until response is gathered.
            else:
                self.dbg.m("skipping the blockade on the first run. to avoid wrong debug messages.", cdb = 1)

            if (self.comm_working == False):
                self.dbg.m("comm handle request start. waiting for request.", cdb=1)
                self.comm_handle_requests()

    def request(self, request_tuple, cbt=0):
        self.dbg.m("adding request_BEFORE:",request_tuple,cdb=11)
        _n = list(request_tuple)
        self.__addRequest(request_tuple, cbt)

    def get_response(self,calling_thread_var=""): # just a check variable that not the wrong thread does steal the information
        # this identifies the calling thread and gives the
        if calling_thread_var == "": return False,("calling thread var is empty")
        _worked, _answertuple = self.__getrem_retval_exists(calling_thread_var)
        if not _worked: return False,('key does not exist')
        self.dbg.m("get_response:",calling_thread_var, "==",self.comm_rspTo,cdb=3)
        self._this_response_request_by = calling_thread_var
        retval = self.comm_rspTo
        _r = self.__getrem_retval()
        self.__response_gathered()
        self.dbg.m("get_response:",_r,cdb=2)
        return True,(_r)

    def response_available(self,for_who=""):
        _x, _m = self.__getrem_retval_exists(for_who)
        self.dbg.m("response_available:",_x,"//msg:",_m,"//for:",for_who,cdb=11)
        if _x: return True, (_x,_m)
        return False, (_x,_m)

    def __reset_output_queue(self,w):
        self.comm_rspListDict = []
        pass
        #del

    def __comm_handle_output_watcher(self):
        pass
        #cheeck the output for duplicates.
        #if there are, remvoe all outputs and maybe restart the modul which did produce the error...

    def __comm_handle_exec_list_has_elements(self):
        print("(len(self.comm_req)):",(len(self.comm_req)))
        return (len(self.comm_req))

    def __comm_handle_pre_check(self,dir=0) -> None:
        if not self.__comm_handle_exec_list_has_elements(): return self.comm_handle_requests(dir=0,reent=True)# no work, what am i even doing here.
        cmd = copy.deepcopy(self.comm_req)#self.comm_req.pop(dir) # check with a copy to avoid confusion in the list..
        try:
            cmd = cmd.pop(dir)
        except Exception as e:
            self.dbg.m('__comm_handle_pre_check -> cmd.pop(dir):',e,cdb=-7)
            return self.comm_handle_requests(dir=0,reent=True)


        _response_for_ident_exists, _ret = self.__getrem_retval_exists(cmd[-1])
        if (_response_for_ident_exists):
            self.dbg.m(f"comm_handle_requests(ident='{cmd[-1]}'): has output waiting in queue - waiting")
            list_size = len(cmd)-1
            if (list_size > 1):
                self.dbg.m(f"comm_handle_requests(list_size > 1({str(list_size)}):TRUE) calling: 'comm_handle_requests(dir=-1)'")
                return self.comm_handle_requests(dir=-1) # take upper one now.
            else:
                self.dbg.m(f"comm_handle_requests(list_size > 1({str(list_size)}):ELSE) calling: 'comm_handle_requests(dir=0,reent=True)'")
                return self.comm_handle_requests(dir=0,reent=True)# just return to rejoin the loop with hopefully more work or an empty queue.

    def __comm_handle_build_call(self,cmd) -> str:
        _args = [f"{_x}" for _x in cmd if (_x != cmd[0] and _x != cmd[-1])]
        _r = ""
        for i in range(1,len(cmd)-1):
            _r += str(cmd[i])+","
        _r = _r[:-1]
        retVal = ""
        _locals = locals()
        _exec = f"retVal = self.{cmd[0]}( {_r} )"
        return _locals, _exec

    def __comm_handle_call_func(self, _exec, _locals, cmd) -> tuple:
        try:
            exec(_exec, globals(), _locals )
        except Exception as e:
            self.dbg.m("watch your formatting(%s):"%(_exec),e,cdb=-7)
            return self.__setResponse((False,cmd[-1]))
        retVal = (_locals['retVal'],cmd[-1])
        self.dbg.m('_exec:',_exec, cdb=1)
        self.dbg.m('_ret:',retVal[0],cdb=1)
        self.dbg.m('_ret:',retVal[1],cdb=1)
        return retVal

    def __comm_handle_debug_incoming_cmd(self,cmd):
        self.dbg.m("command and args found: ",  cmd,                cdb=2)
        self.dbg.m("command:",                  cmd[0],             cdb=9)
        self.dbg.m("args:",                     cmd[1:len(cmd)-1],  cdb=9)
        self.dbg.m("identifier:",               cmd[-1],            cdb=9)

    def __comm_handle_reset_values_before_exec(self,v=('hrv.jumpers=-1','hrv.rxMillis=-1')):
        if not type(v) == tuple:
            _v = v.split('=')[0]
            print("BEFORE, v:",eval(_v))
            try:
                exec(v)
            except Exception as e:
                self.dbg.m("exception:",e,cdb=-7)
            print("AFTER, v:",eval(_v))
        else: # is tuple...

            return
        pass

    def __comm_handle_reset_working_state(self):
        self.dbg.m('__comm_handle_reset_working_state: resetting',cdb=9)
        self.comm_working = False
        self.comm_getdone = False

    def __comm_handle_request_TTL_passed(self):
        self.dbg.m('TTL Fail of comm handler Entry',cdb=1)
        return self.__setResponse((False,'TTL has been exceeded'))

    def __comm_handle_read_stat_cn_saving(self,cmd):
        if  cmd[-1][-1*(len('ret_log_q')):]  == "ret_log_q": self.__set_buf_log_cn()
        elif cmd[-1][-1*(len('ret_mon_q')):] == "ret_mon_q": self.__set_buf_mon_cn()
        hrv.jumpers  = st.jumpers
        hrv.rxMillis = st.rxMillis
        return self.__setResponse((self.read_stat_str,cmd[-1]))

    def comm_handle_requests(self,dir = 0,reent=False):
        self.comm_firstrun      = False
        list_size               = len(self.comm_req)
        if dir != 0:              self.dbg.m("comm_handle_request recursive entry -dir:",dir,cdb=3)
        if reent != True:         self.dbg.m("list size:",list_size,";data:",self.comm_req,cdb=2)
        _did_pop, __mstr = False, 'comm_handle_requests: begin work with a ttl of '+ str(self.comm_TTL) +' seconds'
        if (list_size > 0):
            self.comm_working = True
            try:
                self.                   __comm_handle_pre_check(dir)
                cmd, _did_pop   = self.comm_req.pop(dir), True

                self.                   __comm_handle_debug_incoming_cmd(cmd)
                self.                   __comm_handle_reset_values_before_exec()
                _locals, _exec  = self. __comm_handle_build_call (cmd)
                retVal          = self. __comm_handle_call_func  (_exec, _locals, cmd)
                if (cmd[0] == 'read_stat'):
                    pan.parse_string()
                    return self.__comm_handle_read_stat_cn_saving(cmd)  ### READ_STAT EXTRAS SO THE VALUES WILL BE BUFFERED CORRECTLY
                else:
                    return self.__setResponse((retVal,cmd[-1]))

            finally:
                self.__comm_handle_reset_working_state()

        if _did_pop and self.__passedTTL(intern_ttl=True):
            return self.__comm_handle_request_TTL_passed()

    def __comm_handle_requester_has_output_to_receive(self,c):
        _t = copy.deepcopy(self.comm_rspListDict)
        if len(_t) < 1: return False
        try:
            _x = _t.pop()
        except Exception as e:
            return False
        try:
            print("_x[c]:",_x[c])
        except Exception as e:
            return False
        self.dbg.m('output found!:',_x,cdb=1)
        return True

    def __set_buf_mon_cn(self):
        hrv.set_cn("m")
        _s = str( {**hrv.cn2_mon, **hrv.cn4_mon} )
        self.dbg.m(f"__set_buf_mon_cn -> hrv.set_cn('m') -> {_s}",cdb=9)

    def __set_buf_log_cn(self):
        hrv.set_cn('l')
        _s = str( {**hrv.cn2_log, **hrv.cn4_log} )
        self.dbg.m(f"__set_buf_log_cn -> hrv.set_cn('l') -> {_s}",cdb=9)

    # RX receiver functions
    def get_rx_response(self):
        x   = "\n"+("-"*30)+"[TERMINAL OUTPUT]:" + self.__rx_response
        x  += "\n\n"+("-"*30)+"[CONSOLE LOG]:\n" + str(self.dbg.get())# self.__set_rx_response(self.dbg.get())
        if x != None:
            self.dbg.m("__get_rx_response:",x,cdb=3)
            self.__reset_rx_response()
            return x
        else:
            self.__reset_rx_response()
            self.dbg.m("__get_rx_response: 'None' (empty)", cdb=3)
            return ""

    def __append_rx_response(self,val,cbt=False):
        if cbt == False:
            return #self.dbg.m("__append_tx_response: not called by terminal",cdb=11)
        if self.__rx_response == None: self.__rx_response = ""
        self.__rx_response += "\n" + str(val)
        self.dbg.m("__append_tx_response:",self.__rx_response,cdb=3)

    def __set_rx_response(self,val):
        self.__append_rx_response( str(val), self.__rx_called_by_terminal )

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
        self.dbg.from_term(False)

    #INTERNAL QUERXY HANDLER functions
    def show(self,w="r"):
        _request_key = "r"
        if w.lower() == _request_key:
            return self.comm_rspListDict

    def __getrem_clear_ident(self,i):
        _exists, _extratuple = self.__getrem_retval_exists(i)
        if _exists:
            i = str(i)
            print("comm_rspListDictB:",self.comm_rspListDict)
            try:
                self.comm_rspListDict.remove(i)
            except Exception as e:
                self.dbg.m("__getrem_clear_ident exception:",e, cdb=-7)
            print("comm_rspListDictA:",self.comm_rspListDict)
            return True

    def __getrem_retval(self):
        _this_req  = self._this_response_request_by
        if _this_req.__class__ == tuple:
            self.dbg.m("__getrem_retval - _this_req=tuple:",_this_req,cdb=1)
            return False
        _found,_w  = self.__getrem_retval_exists(_this_req)
        if _found:
            self.__comm_remove_entry_from_ttl_dict(_this_req)
            return self.__getrem_del_entry(_this_req,_w)
        self.dbg.m(f'__getrem_retval: Sorry no Data in Queue for you {_this_req}', cdb=11)
        return False

    def __getrem_del_entry(self,_this_req,_w,_dflt= 'SORRY_KEY_NO_EXIST'):
        _x = _w         #getattr(_w,_this_req,__default=_dflt)
        _c = _this_req
        if _x == _dflt:
            self.dbg.m(f"__getrem_retval({_c}): __getrem_retval_exists->True, but key empty({_x} == {_dflt})",_x, cdb=3)
            return False
        self.dbg.m(f"__getrem_retval({_c}): ",_x, cdb=3)
        _s = {_c:_x}
        try:
            _cmp = self.comm_rspListDict.index(_s)
        except Exception as e:
            self.dbg.m("__getrem_del_entry Exception:",e,cdb=-7)
            return False # not found in list
        #print("_cmp:",_cmp)
        try:
            #self.comm_rspListDict.remove(_cmp)
            del self.comm_rspListDict[_cmp]
        except Exception as e:
            self.dbg.m("__getrem_del_entry Exception:",e,cdb=-7)
        return _x


    def __getrem_retval_exists(self,_this_req):
        _this_req = str(_this_req)
        if _this_req.__class__ == tuple:
            self.dbg.m("__getrem_retval_exists - _this_req=tuple:",_this_req,cdb=1)
            return False, ("args are a tuple... wrong", 0, 0)

        ### test start
        _f = False
        for _w in self.comm_rspListDict:
            if _this_req in _w: return True, _w[_this_req]
        return False,'key not found'
        ### test end

        #_temp_list = list(self.comm_rspListDict)
        _temp_list = copy.deepcopy(self.comm_rspListDict)
        if len(_temp_list) < 1: return False, ('temp list smaller than 1..', 0, 0)

        self.dbg.m('__getrem_retval_exists: (comm_rspListDict/_this_req):', self.comm_rspListDict, "//",_this_req,cdb=11)
        c=0
        while len(_temp_list) > 0:
            _current = _temp_list.pop(0)
            c+=1
            #for dicts in _current:
            #    if _this_req == dicts:
            #        if not _this_req == "":
            #            self.dbg.m('__getrem_retval_exists: (_this_req in dicts):',_this_req in dicts,cdb=3)
            #            self.dbg.m('_current[_this_req]',_current[_this_req],cdb=3)
            #            return True, (_current[_this_req], _this_req, c)
            if _this_req in _current:
                self.dbg.m('__getrem_retval_exists: (_this_req in dicts):',_this_req in _current,cdb=3)
                self.dbg.m('_current[_this_req]',_current[_this_req],cdb=3)
                return True, (_current[_this_req], _this_req, c)
        return False, 'not exist'

    def __response_empty(self):
        _check, _msg = self.__getrem_retval_exists(self._this_response_request_by)
        self.dbg.m('__response_empty:',_check,"//msg:",_msg,cdb=3)
        if _check != False: return True
        return False

    def __work_available(self):
        self.dbg.m("is work available:", (True if len(self.comm_req)>0 else False), cdb=self.spam_debug_level)
        return True if len(self.comm_req) > 0 else False

    def __addRequest(self,request_tuple,cbt=0):
        #self.__startTTL("__addRequest: START TTL")
        self.dbg.m("__addRequest: entering", cdb = 10)
        self.dbg.m("adding request:",request_tuple,cdb=10)
        if cbt == 1:
            self.set_called_by_terminal()
            self.dbg.from_term(True)
        #gc.disable()
        return self.comm_req.append(request_tuple)
        #gc.enable()

    def __passedTTL(self, intern_ttl=False) -> bool:
        self.dbg.m("__passedTTL: entering", cdb = self.spam_debug_level)
        #if (self.comm_TTL_timer == None     or self.comm_TTL_timer_end      == None): return True
        if (self.comm_TTL_timer_s == None   or self.comm_TTL_timer_s_end    == None): return True
        if intern_ttl != True:
            pass
        else:  #intern ttl manager, to finish a request.
            self.comm_TTL_timer_s = time.time()
            _r = (self.comm_TTL_timer_s > self.comm_TTL_timer_s_end)
            self.dbg.m("__passedTTL:TTL > TTL END - (self.comm_TTL_timer_s > self.comm_TTL_timer_s_end)", _r, cdb=3)#cdb = self.spam_debug_level)
            return _r

    def __startTTL(self,m="",intern_ttl=False):
        if (m != ""): self.dbg.m("__startTTL:",m,cdb=1)
        if intern_ttl != True:
            pass
        else:  #intern ttl manager, to finish a request.
            self.dbg.m("__startTTL: entering [SEND QUEUE TTL]", cdb = 10)
            self.comm_TTL_timer_s     = time.time()
            self.comm_TTL_timer_s_end = self.comm_TTL_timer_s + self.comm_TTL
            self.dbg.m("__startTTL:comm_TTL_timer", self.comm_TTL_timer, "//comm_TTL_timer:",self.comm_TTL_timer, cdb = self.spam_debug_level)


    def __resetTTL(self, intern_ttl=False):
        if intern_ttl != True:
            pass
        else:  #intern ttl manager, to finish a request.
            self.dbg.m("__resetTTL: entering [SEND QUEUE TTL]", cdb = 10)
            self.comm_TTL_timer_s     = None
            self.comm_TTL_timer_s_end = None
            self.dbg.m("__resetTTL:comm_TTL_timer", self.comm_TTL_timer, "//comm_TTL_timer:",self.comm_TTL_timer, cdb = self.spam_debug_level)

    def __comm_check_all_ttls(self):
        try:
            for _w in self.comm_ttl_count_dct.keys():
                if time.time() > float(self.comm_ttl_count_dct[str(_w)]):
                    self.__comm_remove_entry_from_both_lists(_w)
                    self.dbg.m("__comm_check_all_ttls expired:",_w,cdb=2)
        except Exception as e:
            self.dbg.m("__comm_check_all_ttls list changed while TTL check waiting with check:",e,cdb=-7)

    def __comm_remove_entry_from_ttl_dict(self,e):
        try:
            del self.comm_ttl_count_dct[str(e)]
        except Exception as ef:
            self.dbg.m("__comm_remove_entry_from_ttl_dict exception:",ef,cdb=3)
        self.dbg.m("__comm_remove_entry_from_ttl_dict:",e,"//comm_ttl_count_dct:",self.comm_ttl_count_dct,cdb=2)

    def __comm_remove_entry_from_both_lists(self,_this_req):
        _found,_w  = self.__getrem_retval_exists(_this_req)
        if _found:
            self.__getrem_del_entry(_this_req,_w)
            self.__comm_remove_entry_from_ttl_dict(_this_req)
        self.dbg.m("__comm_remove_entry_from_both_lists:",e,"//comm_ttl_count_dct:",self.comm_ttl_count_dct,cdb=2)

    def __comm_set_dict_and_ttl(self, response):
        x = response
        self.dbg.m("RESPONSE: (comm_rsp=%s; comm_rspTo=%s; comm_working=%s; comm_getdone=%s)"%(x[0],x[1],0,False),cdb=3)
        self.comm_rsp       = x[0]
        self.comm_rspTo     = x[-1]
        _entry = dict()
        _kv = str(x[0:-1])
        _id = str(x[-1])
        _entry[_id] = _kv

        if self.__comm_handle_requester_has_output_to_receive(_id) == False:
            self.comm_rspListDict.append(_entry)
            self.comm_ttl_count_dct[str(_id)] = time.time() + self.comm_ttl_count_max
            self.dbg.m("comm_rspListDict:",self.comm_rspListDict,cdb=3)
        else:
            self.queue_failsafe_counter += 1
            self.dbg.m("__comm_handle_requester_has_output_to_receive -> True!",cdb=1)

        if self.queue_failsafe_counter >= self.queue_failsafe_counter_max:#reset all dicts..
            self.dbg.m("__comm_handle_requester_has_output_to_receive -> queue_failsafe_counter=max -> resetting dicts", cdb=1)
            self.comm_rspListDict = []
            self.comm_ttl_count_dct = {}
            self.queue_failsafe_counter = 0
            self.dbg.m(f"comm_rspListDict={self.comm_rspListDict} // comm_ttl_count_dct={self.comm_ttl_count_dct} // queue_failsafe_counter={self.queue_failsafe_counter}", cdb=1)

    def __setResponse(self,response):
        self.dbg.m("__setResponse: entering", cdb = 10)
        self.__comm_set_dict_and_ttl( response )
        _x = 'True' if (type(self.comm_rsp)==type(bool) and self.comm_rsp==True) else 'False'
        _t = _x[:50]#self.comm_rsp[:50] # cut lenght..
        self.__resetTTL(intern_ttl=True) # removee serbus working on TTL
        self.__set_rx_response( '%s -> %s'%(str(self.comm_rsp),str(self.comm_rspTo)) )
        self.comm_working   = False
        self.comm_getdone   = False

    def __response_gathered(self,ttl_pass=False):
        _x = "[TTL HAS BEEN PASSED]" if ttl_pass != False else ""
        self.dbg.m("__response_gathered: entering", cdb = self.spam_debug_level)
        self.dbg.m("__response_gathered():",self.comm_rspTo if (ttl_pass == False) else f"{self.comm_rspTo} -> {_x}",cdb=self.spam_debug_level)
        self.dbg.m("__response_gathered.comm_rsp:",self.comm_rsp,cdb=self.spam_debug_level)
        self.comm_rsp       = ""
        self.comm_rspTo     = ""
        self.comm_working   = False
        self.comm_getdone   = True
        self.comm_firstrun  = False
        self.dbg.m("__response_gathered.__getrem_clear_ident try with:", self._this_response_request_by, cdb=3)
        self.__getrem_clear_ident(self._this_response_request_by)
        self._this_response_request_by = ""

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
        pan.pa_to_ser_obj.add('txrx_command: ' + str(txCmd))
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
        except Exception as e:
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
        pan.pa_to_ser_obj.add('txrx_command -> self.rxCmd: ' + str(self.rxCmd))
        return line

    def net_dialog(self, txCmd, info=0 ):
        pan.pa_to_ser_obj.from_term(self.__rx_called_by_terminal)
        self.dbg.from_term(self.__rx_called_by_terminal)
        pan.pa_to_ser_obj.add('net_dialog: ' + str(txCmd))
        self.txCmd = txCmd
        maxCnt = self.NET_REPEAT
        repeat = 0
        self.tries_last_ping = repeat
        #ready  = False
        try:
            while repeat < maxCnt :
                self.dbg.m("resetting buffer",cdb=9)
                self.ser_reset_buffer()
                self.dbg.m("sending:",txCmd.replace('\n',''), cdb=2)
                self.txrx_command( txCmd )
                self.dbg.m("parsing answer.. entering pan.parse_answer():",cdb=9)
                #self.dbg.m(pan.parse_answer(),cdb=9)
                parse = pan.parse_answer()
                self.__set_rx_response(pan.pa_to_ser_obj.get())
                self.dbg.m("parse_answer return:",parse,cdb=9)
                print(1)
                if parse:
                    print(2)
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

        finally:
            print(3)
            pan.pa_to_ser_obj.from_term(False)
            self.dbg.from_term(False)


    # *****************************************
    # *** module communication commands     ***
    # *****************************************

    def ping(self, modAdr ):
        self.txCmd = mb.wrap_modbus( modAdr, 1, 0, "" )   # cmd==1: send ping
        success,repeat = self.net_dialog(self.txCmd, 1)   # *pl*
        #self.__set_rx_response('txCmd:   %s'%(str(self.txCmd)))
        #self.__set_rx_response('ping success:  %s'%(str(success)))
        #self.__set_rx_response('ping repeat:  %s'%(str(repeat)))
        return success, repeat

    def cnget(self,c=0):
        x,y = hrv.get_cn('')
        return x if (c == 0) else y
        #return self._cn2 if (c == 0) else self._cn4

    def read_stat(self, modAdr, subAdr):#, retry_count=0, skip_first=0 ) :
        h = cg.hkr_obj.get_heizkreis_config(0)
        if len(h) > 5: (self.heizkreis, self.modules, self.modTVor, self.modSendTvor, self.dtLog, self.filtFakt) = h
        else:          (self.heizkreis, self.modules, self.modTVor, self.modSendTvor, self.dtLog, self.filtFakt) = (self.default_values)
        if (modAdr == self.modTVor and subAdr > 1): return False
        ''' read all status values from module
            using command 2 and 4
        '''
        self.__set_rx_response('read_stat(mod=%s,sub=%s)'%(str(modAdr),str(subAdr)))
        # hrv.reset_cn('')

        self.txCmd = mb.wrap_modbus( modAdr, 2, subAdr, "" )
        if not self.net_dialog(self.txCmd):
            #_set_cn2_cn4_err('ser_read_stat','args:2')
            return False

        time.sleep(0.01)
        self.txCmd = mb.wrap_modbus( modAdr, 4, subAdr, "" )
        if not self.net_dialog(self.txCmd):
            #_set_cn2_cn4_err('ser_read_stat','args:4')
            return False
        f=2#self.dbg.const( "__DBG_LVL_FUNCTIONS_AND_RETURN" )
        self.dbg.m("cn2:",cn2,"cn4:",cn4,cdb=f)
        self.dbg.m("cn2_ser:",cn2_ser,"cn4_ser:",cn4_ser,cdb=f)

        _cn2, _cn4 = hrv.get_cn('s')

        self.get_milisec(modAdr)
        self.dbg.m("get_milisec():",st.rxMillis,cdb=f)
        self.get_jumpers(modAdr)
        self.dbg.m("get_jumpers():",st.jumpers,cdb=f)
        # module data:
        self.cmdHead  = "0002%02X%db "%(int(modAdr),int(subAdr))
        self.tic      = float(st.rxMillis) / 1000.0
        self.ticStr   = "t%.1f "%(self.tic)

        #cn2={"SN":0,"VM":0,"RM":0,"VE":0,"RE":0,"RS":0,"PM":0}
        self.vlMeas   = float(_cn2["VM"])
        self.rlMeas   = float(_cn2["RM"])
        self.vlEff    = float(_cn2["VE"])
        self.rlEff    = float(_cn2["RE"])
        self.rlSoll   = float(_cn2["RS"])
        self.posMot   = float(_cn2["PM"])

        #cn4={"ER":0,"FX":0,"MT":0,"NL":0} # command names
        self.erFlag  = int(_cn4["ER"])
        self.fixPos  = float(_cn4["FX"])
        self.motTime = float(_cn4["MT"])
        self.nLimit  = int(_cn4["NL"])

        s1    = "VM%5.1f RM%5.1f VE%5.1f RE%5.1f "%(self.vlMeas,self.rlMeas,self.vlEff,self.rlEff)
        s2    = "RS%5.1f P%03.0f "%(self.rlSoll, self.posMot)
        s3    = "E%04X FX%.0f M%.0f A%d"%(self.erFlag,self.fixPos,self.motTime,self.nLimit)
        # FX muss noch übersetzt werden.
        x = s1 + s2 + s3
        self.read_stat_str = str(self.cmdHead) + str(self.ticStr) + \
                                str(_cn2["SN"]) + " " + str(x)
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
            self.dbg.m("cn2=",str(self._cn2),cdb=1)
            self.dbg.m("cn4=",str(self._cn4),cdb=1)
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
            self.vlMeas   = float(self._cn2["VM"])
            self.rlMeas   = float(self._cn2["RM"])
            self.vlEff    = float(self._cn2["VE"])
            self.rlEff    = float(self._cn2["RE"])
            self.vlrl     = "VM%5.1f RM%5.1f VE%5.1f RE%5.1f "%(self.vlMeas,self.rlMeas,self.vlEff,self.rlEff)
            self.log_data_string = self.header + self.cmdHead + self.ticStr + str(self._cn2["SN"]) + " " + self.vlrl
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

def ser_get_work( q, ttl = 3 ):
    global ser_obj, pa
    _ttlm       = time.time() + ttl
    while True:
        _rsp, _val  = ser_obj.response_available()
        print("_rsp:",_rsp)
        print("(time.time() > _ttlm):", (time.time() > _ttlm))
        if (time.time() > _ttlm):
            return False, ("TTL of 3 seconds passed.")
        if _rsp:
            break
        time.sleep(0.01)

    if _rsp:
        try:
            return ser_obj.get_response(q)
        except Exception as e:
            ser_obj.dbg.m("ser_get_work Exception:", e, cdb=-7)
        return False, ('No values found for:', q)

    return False, ("No response available for:",q)

def ser_add_work( t:tuple, blocking=True, cbt=0, logger_r = False, mon_r = False ):
    global ser_obj, pa
    _ttl_break = False
    _err = ""

    #if (cbt == 0 and logger_r == False and mon_r == False):    #un and repack old requests until the rest of the code is aligned
    _IDENTIFIER_ = _rnd(5) + 'SER_ADD_WORK_RND' + _rnd(15)
    if (cbt or logger_r or mon_r): _IDENTIFIER_ += t[-1]
    t = list(t)
    t[-1] = _IDENTIFIER_
    t = tuple(t)
    print("t:",t)

    if blocking != True:
        ser_obj.request(t,cbt)
        return t[-1] # give back identifier on non blocking mode
    #mydict = dict((y, x) for x, y in t) ("fucntion name",a,n,identifier)
    ser_obj.request(t,cbt)
    _l_internal_receival_timer_end = time.time() + ser_obj.comm_TTL # maximum wait for response time...
    while True:   # wait for answer            # in response_available has to be added a TTL value.
        _response_avail, _msg_tuple = ser_obj.response_available(t[-1])
        if (time.time() > _l_internal_receival_timer_end):
            _t = str(t)
            _err = f'ser_add_work: TTL of {ser_obj.comm_TTL}s passed for request ({_t}); _msg_tuple: ({_msg_tuple[0]}/{_msg_tuple[1]})'
            ser_obj.dbg.m(_err,cdb=1)
            _ttl_break = True
            break
        if _response_avail:
            break
        time.sleep(0.01)
    ser_obj.dbg.m('ser_add_work - _msg_tuple:',_msg_tuple,cdb=3)

    r = ser_obj.get_response(t[-1])
    if _ttl_break: return False, _err
    if r[0] == False:
        _err = "error running: "+str(t)+" //err_msg:"+str(r[1])
        _t,_r = str(t),str(r[1])
        _err = f'ser_add_work: error running ({_t}) return: ({_r})'
        ser_obj.dbg.m(_err,cdb=1)
        return False, _err
    ser_obj.__rx_called_by_terminal = False
    return True, r

def _rnd(length):
    result_str = ""
    for i in range(length):
        letters     = string.ascii_lowercase            if (random.randint(0,1) == 0) else string.ascii_uppercase
        result_str += ''.join(random.choice(letters))   if (random.randint(0,1) == 0) else ''.join(random.choice("1234567890"))
    return result_str

def ser_add_work_test(t:tuple, blocking=True, cbt=0):
    _w, _v = ser_add_work(t, blocking, cbt)
    print("ser_add_work_test:",_w,"//",_v)
    return _v
    eval('self.'+key+'()')

if __name__ == "__main__":
    ser_obj.ser_check()

    x= "SERBUS_MAIN_IDENTIFIER"
    modAdr = 4
    subAdr = 1

    r = ("read_stat",modAdr,1,x)
    er = ser_add_work( r )
    print("ser_obj.comm_rspListDict:",er)

    r = ("read_stat",modAdr,3,x)
    e = ser_add_work( r  )
    print("ser_obj.comm_rspListDict:",er)
    if not r == False:
        #ser_obj.dbg.m("got cn2+cn4 -> deepcopy into log_obj.cn2/cn4.",cdb=2)
        #ser_obj.dbg.m("log_obj.cn2:", lg.log_obj._cn2,cdb=9) # 9 = verbose debug
        #ser_obj.dbg.m("log_obj.cn4:", lg.log_obj._cn4,cdb=9) # 9 = verbose debug
        pass
    else:
        ser_obj.dbg.m("error getting cn2 and cn4",cdb=2)

    pass

    os.system('cls')
    ser_ident = [1,2,3]
    mods = [*range(1,5)]
    work = [("read_stat",e,z,str(z*e)) for z in ser_ident for e in mods]
    print("WORK:",work)
    #produce error, cause we dont get the queue response:
    er = ser_add_work(('read_stat',1,1,'1'), blocking =False)
    _lw = []
    print("STARTING WORKERS")
    for x in work:
        # create workers:
        #print("x:",x)
        _w = th.Thread(target=ser_add_work_test, args=((x),True,0))
        _w.setDaemon(True)
        _lw.append(_w)
        #print ('_lw',_lw)
        try:
            _w.start()
        except Exception as e:
            print("Exception:",e)

    while len(_lw)>0:
        for threads in _lw:
            if not threads.is_alive(): _lw.remove(threads)
        time.sleep(0.01)

    while True:
        time.sleep(0.25)
        pass
    print("DONE")

