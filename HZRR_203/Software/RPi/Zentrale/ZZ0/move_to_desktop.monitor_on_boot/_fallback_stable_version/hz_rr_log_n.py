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

import threading as th
import platform
import time
import copy
import heizkreis_config as hkr_cfg
import hr2_variables as hrv
import hz_rr_config as cg
import hz_rr_debug as dbg
import usb_ser_b as us

global log_obj


def wait(s):
    pass
    # print(s)
    # time.sleep(2.0)


class Log():
    valve_not_moving_timer = modules = odat = vlZen = vle1 = filtFakt = heizkreis = \
        modTVor = p = outFileName = locPath = modAdr = cn2 = cn4 = \
        txCmd = rxCmd = modSendTvor = ctrIdx = None
    ret_log_q = "ret_log_q"
    dbg = dbg.Debug(1)

    max_not_moving_time = int(cg.conf_obj.r('LOGGER-SETTINGS',                      'valve_motor_failsafe_timer', 60*10))
    valve_not_moving_timer = time.time() + max_not_moving_time

    linux = 0
    if platform.system() == "Linux":
        linux=1

    pltpath             = str (cg.conf_obj.r('system', 'logPlotPath',                    'hz_rr_plot10.py'))
    loggerpath          = str (cg.conf_obj.r('system', 'logStartScriptPath',             'hz_rr_log_start2.sh'))
    lmdname             = str (cg.conf_obj.r('system', 'logMonitorDirectPath',           'hz_rr_monitor_direct02_b.py'))
    log_on_usb          = bool(cg.conf_obj.r('system','logOnUSB',                       'True'))
    log_on_usblnx       = str (cg.conf_obj.r('system', 'logPath_USB_LINUX',              '/media/pi/PYTHONUSB/move_to_desktop.monitor_on_boot/log/'))
    log_on_usbwin       = str (cg.conf_obj.r('system', 'logPath_USB_WIN',                'D:\\coding\\move_to_desktop.monitor_on_boot\\log\\'))
    logPathlnx          = str (cg.conf_obj.r('system', 'logPath_local_LINUX',            '/home/pi/Desktop/Monitor/PYTHONUSB/log/'))
    logPathwin          = str (cg.conf_obj.r('system', 'logPath_local_WIN',              'D:\\coding\\move_to_desktop.monitor_on_boot\\log\\'))
    pos_dif             = int (cg.conf_obj.r('LOGGER-SETTINGS', 'max_pos_difference',     3))
    neg_dif             = int (cg.conf_obj.r('LOGGER-SETTINGS', 'max_neg_difference',    -3))
    move_time           = int (cg.conf_obj.r('LOGGER-SETTINGS', 'max_valve_calib_runtime', 1000))  # in ini hinzufügen
    def_soll            = int (cg.conf_obj.r('LOGGER-SETTINGS', 'default_soll_value',    44.0))
    nano_valve_assistant= bool(cg.conf_obj.r('LOGGER-SETTINGS', 'nano_valve_assistant',   True))

    if not log_on_usb:
        locPath     = logPathlnx    if linux==1 else logPathwin
    else:
        locPath     = log_on_usblnx if linux==1 else log_on_usbwin

    dbg.m("logging to:", locPath)
    fn = time.strftime(locPath+cg.conf_obj.r('system', 'logFileNameMask'))

    dbg.m("new file:", fn)
    try:
        odat = open(fn, 'w')
    except Exception as e:
        dbg.m("error opening file:", fn, "\r", "err:", e)
    odat.close()

    # some initial values
    filtFakt = 0.1    # Filter 2. Ordnung; filtFakt = Bewertung des neuen Wertes
    vlZen = 0.0       # temperature from Zentrale Vorlauf; 0 -> no temperature
    vle1 = 0.0       # initial value
    modAdr = 4
    subAdr = 1

    def __init__(self):
        self._first_run     = 1

    def __del__(self):
        self.dbg.ru()

    def check_log_file(self):
        x = self.outFileName
        if x == "" \
                or self.odat.closed:  # open new file
            self.outFileName = self.locPath+'logHZ-RR_' + \
                time.strftime('%Y%m%d_%H%M%S.dat')
            self.odat = open(self.outFileName, 'w')

    def block_log_until(self,ttl=20):
        beginat=time.time()
        end_time = us.ser_obj.block_log_until_TTL + ttl
        while us.ser_obj.logger_pause == True:
            if time.time()>end_time:
                self.dbg.m("block_log_until: TTL passed, took:",end_time-beginat,"secs.",cdb=1)
                us.ser_obj.logger_pause=False
            time.sleep(0.01)


    def write_all_stat(self):
        for self.modAdr in self.modules:
            self.modIdx = self.modAdr - 1
            for self.ctrIdx in range(3):

                self.block_log_until()
                self.contr = self.ctrIdx+1

                x, y = self.logger_read_stat_queue( self.modAdr, self.contr )
                if not x: return False

                logstr = time.strftime('%Y%m%d_%H%M%S ')
                self.dbg.m(str(hrv.st))
                # 20191016_075934 0901 HK2 :0002091a t4260709.0  S VM 46.0 RM 42.5 VE 20.0 RE 42.5 RS 32.2 P074 E0000 FX0 M2503 A135
                logstr += "%02X%02X " % (int(self.modAdr), int(self.contr)) + \
                    "HK%d " % (int(self.heizkreis)) + ":" + str(y[1])
                self.dbg.m('store: %s' % (logstr))
                logwrite = logstr+'\r\n'
                self.odat.write(logwrite)

                if self.modAdr == self.modTVor and self.ctrIdx == 0:
                    # determine Vorlauftemperatur from Zentrale
                    # if modTVor == 0 it won't get here because modAdr != 0 any times
                    # ":0002011a t1813989.6  W VM 61.8 RM 47.2 VE 61.8 RE 47.2 RS 41.7 "
                    # "P018 E0000 FX0 M5133 A704"
                    # extract temperature
                    #p=parse.rr_parse( logwrite )
                    # if len(p)  > 16 :
                    #    (self.zDateSec,self.hkr,self.module,self.command,self.control, \
                    #        self.protVer,self.modTStamp,self.summer,self.vlm,self.rlm,self.vle,self.rle, \
                    #        self.rls,self.ven,self.err,self.fix,self.tmo,self.tan) = p
                    #    if self.vlZen == 0.0 :
                    #        self.vle1  = self.vle
                    #        self.vlZen = self.vle
                    #    # low-pass filter of order 2
                    #    self.vle1  = self.vle *self.filtFakt + self.vle1 *(1-self.filtFakt)
                    #    self.vlZen = self.vle1*self.filtFakt + self.vlZen*(1-self.filtFakt)
                    # low-pass filter of order 2
                    self.vle = self.cn2["VM"] # self.cn2["VM"]       #
                    if self.vlZen == 0:             # first value
                        self.vle1 = self.vle        # preset filter
                        self.vlZen = self.vle
                    else:
                        self.vle1 = self.vle * self.filtFakt + \
                            self.vle1 * (1-self.filtFakt)
                        self.vlZen = self.vle1*self.filtFakt + \
                            self.vlZen*(1-self.filtFakt)

            self.odat.flush()

    def send_all_Tvor(self, vlZen):
        # Geaendert 20180514: Durch eine extreme Wetterlage mit (Nacht <10deg, Tag >25deg)
        # wurde dauernd zwischen Sommer- und Winterbetrieb umgeschaltet.
        # Dies lief ueber einen laengeren Zeitraum, weshalb es auffaellt.
        # Eine Aenderung der urspruenglichen Regeln zum Verhalten der Regler ist
        # notwendig und moeglicherweise damit eine Umprogrammierung der Regler-software.
        # Als schnelle Massnahme wird die von der Zentrale an die Regler gemeldete
        # Vorlauftemperatur daher stets ueber dem Wert fuer Umschaltung zum
        # Sommerbetrieb gehalten. Diese ist derzeit auf 40 degC eingestellt.
        # Daher wird die zentrale Vorlauftemperatur auf mindestens 44 degC eingestelt.
        for modAdr in self.modSendTvor:
            tempSend = vlZen
            # tempSend = max(vlZen, 44.0)   # (1) sende mindest Temperatur, ueber Sommerbetrieb
            # heisser Sommer; Regler pendeln mit obiger Einstellung
            # zwischen Sommer- und Winterbetrieb
            # Versuch einer Abhilfe durch dauerndes Sommerbetrieb Schalten
            # es wird konstant 20.0 Grad Vorlauf gesendet (unter 30 Grad ist Sommer)
            # FIXME
            # tempSend = 20.0   # (1) sende mindest Temperatur, ueber Sommerbetrieb
            self.dbg.m("send_Tvor to:", modAdr, "//msg:", tempSend, cdb = 2)
            self.logger_send_tvor_queue(modAdr,tempSend)
        pass

    def logger_send_tvor_queue(self,m,vorlauf_send):
        us.ser_obj.request(("send_tvor", m, vorlauf_send, self.ret_log_q))
        while not us.ser_obj.response_available(self.ret_log_q):   # wait for answer            # in response_available has to be added a TTL value.
            pass
        r = us.ser_obj.get_response(self.ret_log_q)
        if r == False:
            self.dbg.m("error sending tvor",cdb=2)
            return r
        self.dbg.m("tvor has been send.",cdb=2)
        return True

    def logger_read_stat_queue(self,moda,ctra):
        us.ser_obj.request(("read_stat",moda,ctra,self.ret_log_q))
        while not us.ser_obj.response_available(self.ret_log_q):   # wait for answer            # in response_available has to be added a TTL value.
            pass
        r = us.ser_obj.get_response(self.ret_log_q)
        if r[0] == False:
            self.dbg.m("error getting cn2 and cn4",cdb=2)
            return r, False
        self.cn2      = copy.deepcopy(us.ser_obj._cn2)
        self.cn4      = copy.deepcopy(us.ser_obj._cn4)
        self.dbg.m("got cn2+cn4 -> deepcopy into log_obj.cn2/cn4.",cdb=2)
        self.dbg.m("log_obj.cn2:", self.cn2,cdb=9) # 9 = verbose debug
        self.dbg.m("log_obj.cn4:", self.cn4,cdb=9) # 9 = verbose debug
        return True, r

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
                h = hkr_cfg.get_heizkreis_config(0)
                if len(h) > 5:
                    #    (heizkreis, modules, modTVor, modSendTvor, dtLog, filtFakt) = h
                    (self.heizkreis, self.modules, self.modTVor,
                    self.modSendTvor, self.dtLog, self.filtFakt) = h
                else:
                    #   # some default values
                    #   heizkreis   = 0q
                    #   modules     = []
                    #   modTVor     = 0
                    #   modSendTvor = []
                    #   dtLog       = 180    # time interval to log a data set
                    #   filtFakt    = 0.1
                    self.heizkreis      = 0
                    self.modules        = 0
                    self.modTVor        = 0
                    self.modSendTvor    = []
                    self.dtLog          = 180
                    self.filtFakt       = 0.1

                nextTime = time.time() + dtLog

                # retreive and write all data in status file
                self.write_all_stat()

                # (1) geaendert 20180514:
                # alt:
                # if modTVor > 0 and vlZen >= 40.0 :
                #   do not send if no T.vl measured or VL Temp. is too low
                # neu:
                if int(self.modTVor) > 0:
                    # Modul f. VLTemp spezifiziert; 0=kein Modul
                    self.dbg.m("self.modTVor > 0:", self.modTVor,
                            " - sending:", self.vlZen, cdb=1)
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


dbg = dbg.Debug(1)
def _check_dif_soll_rueck():
    cur_time = time.time()
    dbg.m("_check_dif_soll_rueck: waiting ",int(log_obj.valve_not_moving_timer-cur_time),"s",cdb=3)
    if (cur_time > log_obj.valve_not_moving_timer): # wir wollen checken ob die temperaturen drastisch unterschiedlich sind.
        dbg.m("_check_dif_soll_rueck: timer has passed.",cdb=1)
        for mod in log_obj.modules:
            for reg in range(1,4):
                logq        = "ret_mon_valve_failback"
                x, y        = us.ser_add_work( ("read_stat",mod,reg,logq) )
                ex          = copy.deepcopy(hrv.cn2)
                rueck       = ex['RM']
                soll        = ex['RS']
                if (soll == 0): soll = log_obj.def_soll
                dif         = rueck - soll
                move_dir    = 0 if (dif > log_obj.pos_dif) else 1 # 1open, 0close
                if (rueck<(soll+log_obj.neg_dif)): move_dir = 1 # we want to open!
                if (rueck>(soll+log_obj.pos_dif)): move_dir = 0 # we want to close

                dbg.m("rücklauf(%s)(<%s?%s):"%(str(soll),str(soll+log_obj.neg_dif),str(rueck<(soll+log_obj.neg_dif))) ,         rueck,
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
                    x = us.ser_add_work( call )
                    dbg.m("ser_add_work(%s): ->"%(str(call)),x,cdb=2)
                    dbg.m("ser_add_work(%s): ->"%(str(call)),x,cdb=-5)
                else:
                    dbg.m("ELSE occured: ((soll == 0) or (rueck < 44) or (dif > log_obj.pos_dif) or (dif < log_obj.neg_dif))",cdb=-5)
                log_obj.valve_not_moving_timer = time.time() + log_obj.max_not_moving_time







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



