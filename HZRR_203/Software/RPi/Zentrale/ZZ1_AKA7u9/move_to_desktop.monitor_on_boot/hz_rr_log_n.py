#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
HZ-RR012 log function

Created on 06.12.2016
@author: Peter Loster (pl)

history:
hz_rr_log.py         06.12.2016  pl  initial release
hz_rr_log_Winter.py  14.05.2018  pl  (1) Simulation hoehere VL Temp
                                     fuer ganzjaehrigen Winterbetrieb
                                     send_all_Tvor() geaendert
                     Nur vorlaeufig - Ergebnis beobachten
hz_rr_log.py         27.07.2018  pl/bd  Sende permanent 20 Grad -> Sommerbetrieb
                     NUR VORLAEUFIG !!!
hz_rr_log.py         22.10.2019  pl/bd Winterbetrieb wieder aktiviert
hz_rr_log.py         30.11.2019  pl    Statusausgabe '.' jetzt ohne Zeilenschaltung
"""

import platform
import time
import copy
import threading        as th
import hr2_variables    as hrv
import hz_rr_config     as cg
import hz_rr_debug      as dbg
import usb_ser_b        as us
from hr2_variables import get_cn_d

global log_obj

class Log():
    def __init__(self):
        self.valve_not_moving_timer =self.modules =self.odat =self.vlZen =self.vle1 =self.filtFakt =self.heizkreis =\
            self.modTVor =self.p =self.outFileName =self.locPath =self.modAdr =\
                self.txCmd =self.rxCmd =self.modSendTvor =self.ctrIdx = None
        self._cn2, self._cn4        = hrv.get_cn('l')
        self.dbg                    = dbg.Debug(1)
        self.max_not_moving_time    = int(cg.conf_obj.r('LOGGER-SETTINGS', 'valve_motor_failsafe_timer',    60*10))
        self.valve_not_moving_timer = time.time() + self.max_not_moving_time
        self.pltpath                = str (cg.conf_obj.r('system',          'logPlotPath',                      'hz_rr_plot10.py'))
        self.loggerpath             = str (cg.conf_obj.r('system',          'logStartScriptPath',               'hz_rr_log_start2.sh'))
        self.lmdname                = str (cg.conf_obj.r('system',          'logMonitorDirectPath',             'hz_rr_monitor_direct02_b.py'))
        self.log_on_usb             = bool(cg.conf_obj.r('system',          'logOnUSB',                         'True'))
        self.log_on_usblnx          = str (cg.conf_obj.r('system',          'logPath_USB_LINUX',                '/media/pi/PYTHONUSB/move_to_desktop.monitor_on_boot/log/'))
        self.log_on_usbwin          = str (cg.conf_obj.r('system',          'logPath_USB_WIN',                  'D:\\coding\\move_to_desktop.monitor_on_boot\\log\\'))
        self.logPathlnx             = str (cg.conf_obj.r('system',          'logPath_local_LINUX',              '/home/pi/Desktop/Monitor/PYTHONUSB/log/'))
        self.logPathwin             = str (cg.conf_obj.r('system',          'logPath_local_WIN',                'D:\\coding\\move_to_desktop.monitor_on_boot\\log\\'))
        self.pos_dif                = int (cg.conf_obj.r('LOGGER-SETTINGS', 'max_pos_difference',               3))
        self.neg_dif                = int (cg.conf_obj.r('LOGGER-SETTINGS', 'max_neg_difference',               -3))
        self.move_time              = int (cg.conf_obj.r('LOGGER-SETTINGS', 'max_valve_calib_runtime',          1000))  # in ini hinzufügen
        self.def_soll               = int (cg.conf_obj.r('LOGGER-SETTINGS', 'default_soll_value',               44.0))
        self.nano_valve_assistant   = bool(cg.conf_obj.r('LOGGER-SETTINGS', 'nano_valve_assistant',             True))
        self.min_vlf_temp_to_send   = int (cg.conf_obj.r('LOGGER-SETTINGS', 'min_vlf_temp_to_send',             20))
        self.max_vlf_temp_to_send   = int (cg.conf_obj.r('LOGGER-SETTINGS', 'max_vlf_temp_to_send',             100))
        self.send_vorlauf_temp_to   = cg.conf_obj.r('nano_valve_assistant', 'send_to_regler',                   "1,3")
        self.set_send_tvor          = cg.conf_obj.r('SEND_TVOR_MODIFIER',   'set_send_tvor',                    'VM')
        self.default_values         = (0,0,0,[],180,0.1)
        self.ret_log_q              = "ret_log_q"
        self.vle                    = 0.0

        if not self.log_on_usb:
            self.locPath     = self.logPathlnx    if (cg.tb.islinux()) else self.logPathwin
        else:
            self.locPath     = self.log_on_usblnx if (cg.tb.islinux()) else self.log_on_usbwin
        _msk = "%__HSTNAME__%"
        _a   = cg.conf_obj.r('system', 'hostPath', "NOTDEF")
        _hst = cg.hkr_obj._get_hostname()
        self.dbg.m("logPath:", self.locPath, cdb=1)
        _r = cg.conf_obj.r('system', 'logFileNameMaskLogFile', 'nlogHZ-RR_%__HSTNAME__%_%Y%m%d_%H%M%S.dat')
        fn = self.locPath + time.strftime(_r.replace(_msk,_hst))
        self.dbg.m("new nLogHZ:", fn, cdb=1)
        _r = cg.conf_obj.r('system', 'logFileNameMask', 'newLogStart_%__HSTNAME__%_%Y-%m-%d_%H-%M-%S.dat')
        fn = self.locPath + time.strftime(_r.replace(_msk,_hst))
        self.dbg.m("new newLog:", fn, cdb=1)

        try:
            self.odat = open(fn, 'w')
        except Exception as e:
            self.dbg.m("error opening file:", fn, "\r", "err:", e, cdb=-7)
        self.odat.close()


        self._first_run     = 1

    def __del__(self):
        self.dbg.ru()

    def check_log_file(self):
        x = self.outFileName
        if (x == "") or (self.odat.closed):  # open new file
            _msk = cg.tb._get_hostname()[1]
            _hst = cg.tb._get_hostname()[0]
            #_hst = cg.tb._get_hostname(cg.conf_obj.r('system', 'hostPath', "NOTDEF"))
            logfilenamemasklogfile= time.strftime(str(cg.conf_obj.r('system','logFileNameMaskLogFile',
            'nlogHZ-RR_%__HSTNAME__%_%Y%m%d_%H%M%S.dat')).replace(_msk,_hst))
            self.outFileName = self.locPath+logfilenamemasklogfile
            self.odat = open(self.outFileName, 'w')
            self.dbg.__init__()

    def block_log_until(self,ttl=20):
        beginat=time.time()
        end_time = us.ser_obj.block_log_until_TTL + ttl
        while us.ser_obj.logger_pause == True:
            if time.time()>end_time:
                self.dbg.m("block_log_until: TTL passed, took:",end_time-beginat,"secs.",cdb=1)
                us.ser_obj.logger_pause=False
            time.sleep(0.01)

    def __bool_nonetype_format(self,_s):
        if (_s==None):  _s = "None"
        elif (_s==False): _s = "False"
        elif (_s==True):  _s = "True"
        return _s

    def write_all_stat(self):
        if self.vle ==None: self.vle1 = 0.0
        if self.vle1==None: self.vle1 = 0.0
        if self.vlZen==None:self.vlZen= 0.0

        for self.modAdr in self.modules:
            self.modIdx = self.modAdr - 1
            for self.ctrIdx in range(3):

                self.block_log_until()
                self.contr = self.ctrIdx+1

                x, y = self.logger_read_stat_queue( self.modAdr, self.contr )
                if not x: return False
                y = self.__bool_nonetype_format(y)

                logstr = time.strftime('%Y%m%d_%H%M%S ')    # 20191016_075934 0901 HK2 :0002091a t4260709.0  S VM 46.0 RM 42.5 VE 20.0 RE 42.5 RS 32.2 P074 E0000 FX0 M2503 A135
                _u = y[2:-3] if (len(str(y)) > 10) else str(y)
                logstr += "%02X%02X "%(int(self.modAdr),    int(self.contr)) + \
                              "HK%d "%(int(self.heizkreis)) + ":" + _u
                self.dbg.m('store: %s' % (logstr),cdb=1)
                logwrite = logstr+'\r\n'
                try:
                    self.odat.write(logwrite)
                except Exception as e:
                    self.dbg.m('write_all_stat exception:',e,cdb=-7)

                self.vle = hrv.st.log_vm_cpy if (hrv.st.log_vm_cpy>20 and hrv.st.log_vm_cpy<100) else 0
                if ((self.modAdr == self.modTVor) and (self.ctrIdx == 0)):
                    if self.vle != 0: # skip
                        if self.vlZen != 0:             # first value
                            self.dbg.m("write_all_stat BEFORE: ('vle' :", self.vle,
                                                                ", 'vle1' :", self.vle1,
                                                                ", 'vlZen' :", self.vlZen,
                                                                ", 'fFakt' :", self.filtFakt,
                                                                ")", cdb = -6)
                            self.vle1 = self.vle * self.filtFakt + \
                                self.vle1 * (1-self.filtFakt)
                            self.vle1 = self.vle1.__round__(2)
                            self.vlZen = self.vle1 * self.filtFakt + \
                                self.vlZen*(1-self.filtFakt)
                            self.vlZen = self.vlZen.__round__(2)
                            self.dbg.m("write_all_stat AFTER:  ('vle' :", self.vle,
                                                                ", 'vle1' :", self.vle1,
                                                                ", 'vlZen' :", self.vlZen,
                                                                ", 'fFakt' :", self.filtFakt,
                                                                ")", cdb = -6)
                        else:
                            self.vle1 = self.vle        # preset filter
                            self.vlZen = self.vle
                    else:
                        self.dbg.m("write_all_stat error:  ('vle' :", self.vle,
                                                            ", 'vle1' :", self.vle1,
                                                            ", 'vlZen' :", self.vlZen,
                                                            ", 'fFakt' :", self.filtFakt,
                                                            ", 'message': 'VLE = 0, SKIPPING')", cdb = -6)
                        #else:
                    #    self.vle1 = self.vle * self.filtFakt + \
                    #        self.vle1 * (1-self.filtFakt)
                    #    self.vlZen = self.vle1*self.filtFakt + \
                    #        self.vlZen*(1-self.filtFakt)

            self.odat.flush()

    def send_all_Tvor(self, vlZen):
        for modAdr in self.modSendTvor:
            self.vle = hrv.st.log_vm_cpy
            tempSend = vlZen
            if self.vle != 0: # no actual Vorlauf temp. -> skip
                if (tempSend > self.min_vlf_temp_to_send and tempSend < self.max_vlf_temp_to_send):
                    x,y = self.logger_send_tvor_queue(modAdr,tempSend)
                    if x==True:
                        self.dbg.m("send_all_Tvor:", modAdr, ",", tempSend, " ->",x ,">> SEND", cdb = 1)
                    else:
                        self.dbg.m("send_all_Tvor:", modAdr, ",", tempSend, " ->",x ,">> NOT SEND", cdb = -6)

                else:
                    _big_check = ((tempSend > self.min_vlf_temp_to_send) and (tempSend < self.max_vlf_temp_to_send))
                    self.dbg.m("send_all_Tvor:", modAdr, ",", tempSend,
                        f" -> [({tempSend}>({self.min_vlf_temp_to_send})={(tempSend > self.min_vlf_temp_to_send)})",
                        f"&& ({tempSend}<({self.max_vlf_temp_to_send})={(tempSend < self.max_vlf_temp_to_send)})]={_big_check} >> NOT SEND", cdb = -6)
            else:
                _big_check = ((tempSend > self.min_vlf_temp_to_send) and (tempSend < self.max_vlf_temp_to_send))
                self.dbg.m("send_all_Tvor:", modAdr, ",", tempSend,
                    f" -> self.vle != 0: {self.vle}", cdb = -6)

        pass

    def logger_send_tvor_queue(self,m,vorlauf_send):
        _q = ("send_Tvor", m, vorlauf_send, self.ret_log_q)
        _work, retv = us.ser_add_work(_q,logger_r=True)
        print("_work:",_work)
        print("retv:",retv)
        if _work == False: # give back default variables
            self.dbg.m("logger_send_tvor_queue ->fail _work:",_work," - resetting cn(l)",cdb=1)
            return False,retv[1]
        return True,retv

    def logger_read_stat_queue(self,moda,ctra):
        _q  = ("read_stat",moda,ctra,self.ret_log_q)
        _work, _retv = us.ser_add_work(_q,logger_r=True)
        if _work== False: # give back default variables
            hrv.reset_cn('l')
            self.dbg.m("logger_read_stat_queue _work:",_work," - resetting cn(l)",cdb=1)
        x, y                = hrv.get_cn('l')
        if (moda == self.modTVor and ctra == 1):
            hrv.st.log_vm_cpy   = x[self.set_send_tvor]
            self.vle            = x[self.set_send_tvor]
        z   = _retv[1]# <<- should be read_stat_str # us.ser_obj.read_stat_str
        self.dbg.m(f"logger_read_stat_queue: (vle={self.vle}) z:",z,cdb=3)
        return True, z

    def rr_log(self):
        us.ser_obj.logger_run = 1
        try:
            r = 1
            math = cg.conf_obj.r('system', 'logFileTime').split("*")
            for zahl in math:
                r *= float(zahl)
            dtNewFile   = float(r)    # 60.0*60.0*6.0    # sec; to make a new file
            dtLog       = float(cg.conf_obj.r('system', 'logTime'))  # 60.0 #* 3.0      # sec; log interval; default value
            timeNewFile = time.time() + dtNewFile
            ende = False
            # task loop (forever)
            while not ende:
                self.block_log_until()
                self.check_log_file()
                h = cg.hkr_obj.get_heizkreis_config(0)
                if len(h) > 5: (self.heizkreis, self.modules, self.modTVor, self.modSendTvor, self.dtLog, self.filtFakt) = h
                else:          (self.heizkreis, self.modules, self.modTVor, self.modSendTvor, self.dtLog, self.filtFakt) = (self.default_values)

                nextTime = time.time() + dtLog
                self.write_all_stat()

                if int(self.modTVor) > 0: # Modul f. VLTemp spezifiziert; 0=kein Modul
                    self.dbg.m("self.modTVor:", self.modTVor,"-> sending:", self.vlZen, cdb=1)
                    self.send_all_Tvor(self.vlZen)

                while (time.time() < nextTime):
                    time.sleep(1)
                    if self.nano_valve_assistant: _check_dif_soll_rueck()
                    self.dbg.m("rr_log: waiting ",(int(nextTime-time.time())),"s", cdb=1)

                if time.time() > timeNewFile:
                    timeNewFile = time.time() + dtNewFile
                    self.dbg.m("close log-file and start a new one", cdb=1)
                    self.odat.close()
                    self.outFileName = ""
        finally:
            us.ser_obj.logger_run = 0


log_obj = Log()

def _check_dif_soll_rueck():
    _skip_mod   = cg.tb.hostname
    _r          = log_obj.send_vorlauf_temp_to
    _range      = [_r] if not _r.find('r') else _r.replace(' ','').split(',')
    #log_obj.dbg.m("_check_dif_soll_rueck _range:",_range,cdb=3)
    cur_time = time.time()
    log_obj.dbg.m("nano_a: waiting ",int(log_obj.valve_not_moving_timer-cur_time),"s",cdb=1)
    if (cur_time > log_obj.valve_not_moving_timer): # wir wollen checken ob die temperaturen drastisch unterschiedlich sind.
        log_obj.dbg.m("_check_dif_soll_rueck: timer has passed.",cdb=1)
        for mod in log_obj.modSendTvor:
            for reg in _range:
                logq        = "ret_mon_valve_failback"
                x, y        = us.ser_add_work( ("read_stat",mod,reg,logq ) ,logger_r=True)
                log_obj.dbg.m("_check_dif_soll_rueck.us.ser_add_work:",y,cdb=2)
                ex          = hrv.get_cn("l")[0] #copy.deepcopy(us.ser_obj.cnget(0))
                rueck       = ex['RM']
                soll        = ex['RS']
                if (soll == 0): soll = log_obj.def_soll
                dif         = rueck - soll
                move_dir    = 0 if (dif > log_obj.pos_dif) else 1 # 1open, 0close
                if (rueck<(soll+log_obj.neg_dif)): move_dir = 1 # we want to open!
                if (rueck>(soll+log_obj.pos_dif)): move_dir = 0 # we want to close

                log_obj.dbg.m("rücklauf(%s)(<%s?%s):"%(str(soll),str(soll+log_obj.neg_dif),str(rueck<(soll+log_obj.neg_dif))) ,         rueck,
                        ";soll(==0?%s):"%(          str(soll==0)),          soll,
                        ";dif(>%s?%s||<%s?%s):"%   (str(log_obj.pos_dif),   str(dif>log_obj.pos_dif),
                                                    str(log_obj.neg_dif),   str(dif<log_obj.neg_dif)),        dif,
                        ";move_dir:",move_dir,
                        ";move_time:",log_obj.move_time,
                        ";pos_dif:",log_obj.pos_dif,
                        ";neg_dif:",log_obj.neg_dif,
                        ";range(%s-%s):"%(          str(int(soll+log_obj.neg_dif)),str(int(soll+log_obj.pos_dif))),
                                                   (str(int(log_obj.pos_dif)+int(log_obj.neg_dif)*-1)) , cdb=-5 )
                if ((soll == 0) or (rueck < 44) or (dif > log_obj.pos_dif) or (dif < log_obj.neg_dif)): # dann wollen wir regeln, weil unterschied +/-3 und scheinbar ein ventil nicht geregelt wird
                    call = ('valve_move',mod, reg, log_obj.move_time, move_dir, logq)
                    x = us.ser_add_work( call ,logger_r=True)
                    log_obj.dbg.m("ser_add_work(%s): ->"%(str(call)),x,cdb=2)
                    log_obj.dbg.m("ser_add_work(%s): ->"%(str(call)),x,cdb=-5)
                else:
                    log_obj.dbg.m("ELSE occured: ((soll == 0) or (rueck < 44) or (dif > log_obj.pos_dif) or (dif < log_obj.neg_dif))",cdb=2)
                    log_obj.dbg.m("ELSE occured: ((soll == 0) or (rueck < 44) or (dif > log_obj.pos_dif) or (dif < log_obj.neg_dif))",cdb=-5)
                log_obj.valve_not_moving_timer = time.time() + log_obj.max_not_moving_time
                return







if __name__ == "__main__":
    print("*****************************")
    print("hz-rr-log")
    print("creating logfile")
    print("*****************************")
    print(log_obj.modules)
    us.ser_obj.ser_check()

    while(True):
        log_obj.rr_log()
        print(us.ser_obj.logger_run)

    us.ser_obj.close()



