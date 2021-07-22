#!/usr/bin/python3
# -*- coding: utf-8 -*-

import os
import stat
import subprocess
import threading
import time
import hz_rr_config as cg
import hz_rr_debug as dbg
from guizero import App, Box, Combo, PushButton, Text
import usb_ser_b as us
import hr2_show_log03c as sl

class Menue():
    def __init__(self):
        self.boxTitle       =       self.textHeadline=  self.boxLogger=     self.textLogger     = \
                self.buttLogOn=     self.buttLogOff=    self.textAction0=   self.textAction     = \
                self.txtLogger0=    self.txtLogger1=    self.txtLogger2=    self.textLoggerB0   = \
                self.textLoggerB1=  self.textLoggerB2=  self.boxScan=       self.app            = self.running_logger= \
                self.buttScan=      self.txtScan0=      self.txtScan1=      self.txtScan2       = self.txtDiagA0=\
                self.textScanB0=    self.textScanB1=    self.textScanB2=    self.textDiagAB1    = self.textDiagAB2=\
                self.boxUeb=        self.buttUeb=       self.txtUeb0=       self.txtUeb1        = self.txtUeb2= \
                self.textUebB0=     self.textUebB1=     self.textUebB2=     self.boxDiagAll     = self.buttDiagAll= \
                self.txtDiagA1=     self.txtDiagA2=     self.textDiagAB0=   self.boxAction= None
        self.monitor_start      = 0
        self.w                  = 800
        self.h                  = 600
        self.pltpath            = cg.conf_obj.r ('system','logPlotPath')
        self.loggerpath         = cg.conf_obj.r ('system','logStartScriptPath')
        self.lmdname            = cg.conf_obj.r ('system','logMonitorDirectPath')
        self.heizkreis          = cg.hkr_obj.get_heizkreis_config()[0]
        self.dbg                = dbg.Debug(1)
        self.dbg.m(str(self.boxTitle))

    def set_perm(self,f):
        try: # output = subprocess.check_output("sudo chmod u+rx " + f).decode("utf-8")
            self.dbg.m("chmod'", f, "'to", stat.S_IRWXU | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
            output = os.chmod(f, stat.S_IRWXU | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
            self.dbg.m(output)
        except Exception as e:
            self.dbg.m("error setting permissions for file ", f)
            self.dbg.m("error: ",e)
        return 0

    def run_bash(self,file):
        self.dbg.m("starting:", file)
        return subprocess.Popen("sudo " + file, shell=True)

    def run_cmd(self,cmd):
        self.dbg.m("executing:", cmd)
        return os.system(cmd)

    def update_status_text(self):
        self.dbg.m(self.textStatus)
        self.textAction.value=self.textStatus
        self.textStatus="<...>"

    def show_textLogger(self, logger ):
        if logger :
            self.textLogger.value = "  Logger AN  "
            self.textLogger.bg    = "lightgreen"
            self.running_logger = True

        else:
            self.textLogger.value = "  Logger AUS  "
            self.textLogger.bg    = "yellow"
            self.running_logger = False

    def set_textLogger(self):
        if us.ser_obj.logger_run==1:
            self.running_logger = True
            self.logger = True
        else:
            self.running_logger = False
            self.logger = False
        self.show_textLogger( self.logger )
        return self.logger


    def but_log_tog(self):
        #threading.Thread(target=self.thr_log_tog).start()
        self.thr_log_tog()

    def thr_log_tog(self):
        lp = us.ser_obj.logger_pause
        if lp == True:
            us.ser_obj.logger_run = 1
            self.logger = True
            us.ser_obj.logger_pause = False
            self.dbg.m("thr_log_tog: LOGGER=ON",cdb=1)
        else:
            self.logger = False
            us.ser_obj.logger_pause = True
            us.ser_obj.logger_run = 0
            self.dbg.m("thr_log_tog: LOGGER=OFF",cdb=1)
        self.show_textLogger( self.logger )

    def runmon(self):
        pass

    def thr_scan_all(self):
        self.textAction.value = "Status aller Module ..."
        if self.mon_obj.monitor_start == 0:
            self.mon_obj.__init__()
            self.mon_obj.runme()
        else:
            self.dbg.m("monitor already running!")
            return 1

        self.textAction.value = "Status beendet"
        time.sleep(0.5)
        self.textAction.value="---"

    def but_scan_all(self):
        self.thr_scan_all()

    def but_terminalG(self):
        self.__but_terminalG()

    def but_terminal(self):
        self.__but_terminal()

    def __but_terminal(self):
        if us.ser_obj.terminal_running==True:
            self.dbg.m("terminal already open",cdb=2)
            return
        us.ser_obj.terminal_running=True
        try:
            self.term_obj.__init__()
            self.term_obj.runme()
        finally:
            us.ser_obj.terminal_running=False

    def __but_terminalG(self):
        if us.ser_obj.terminal_running==True:
            self.dbg.m("terminal already open",cdb=2)
            return
        us.ser_obj.terminal_running=True
        try:
            self.terg_obj.__init__()
            self.terg_obj.runme()
        finally:
            us.ser_obj.terminal_running=False


    def thr_uebersicht(self):
        self.textAction.value="---"
        self.dbg.ru()

    def but_uebersicht(self):
        threading.Thread(target=self.thr_uebersicht).start()

    def thr_diagram_all(self):
        self.textAction.value = "Erstelle Diagramme ..."
        pltpath=cg.conf_obj.r('system','logPlotPath')
        self.dbg.m("pltpath:",self.pltpath,cdb=3)
        sl.runme(99)
        self.textAction.value = "Erstelle Diagramme ... fertig"
        time.sleep(1)
        self.textAction.value="---"

    def but_diagram_all(self):
        threading.Thread(target=self.thr_diagram_all).start()

    def hotfixes(self):
        __fixes = False
        if __fixes:
            self.run_cmd('xhost +local:')
            self.run_cmd("export MPLBACKEND='Agg'")
            self.run_cmd("sudo cp ~/.Xauthority ~root/")
            self.run_cmd("sudo cp /home/pi/.Xauthority ~root/")
            self.dbg.m("done")

    def exit_forcefully(self):
        us.ser_obj.menu_run = 0
        self.app.destroy()
        self.__init__()
        self.draw_menue()

    def draw_menue(self):
        us.ser_obj.menu_run = 1
        try:
            self.hotfixes()
            self.textStatus ="-***-"
            #app = App("HZ-RR Hauptmenü",layout="grid")
            self.app = App(title="HZ-RR Hauptmenü, Heizkreis %s"%(self.heizkreis),width=self.w,height=self.h)
            self.version = "1.0"
            self.hostname = cg.conf_obj.r('system', 'hostPath')

            if cg.conf_obj._tbl.islinux():
                fin = open(self.hostname,"r")
                self.hostname = fin.read().strip()
                fin.close()
            else:
                self.hostname = "WINDOWS"

            self.boxTitle     = Box(self.app,width="fill",align="top",border=True)
            self.textHeadline = Text(self.app, text="%s Menü Rücklauf-Reglung Version %s"%(self.hostname,self.version), align="top", width="fill")

            self.boxLogger    = Box(self.app,width="fill",align="top",border=True)
            self.textLogger   = Text(self.boxLogger, text="-", align="top", width="fill")
            self.buttLogTog   = PushButton(self.boxLogger, text="Logger on/off",         command=self.but_log_tog,  align="left")
            self.buttTerminal = PushButton(self.boxLogger, text="Starte SHELL-Terminal", command=self.but_terminal, align="left")
            self.buttTerminalG= PushButton(self.boxLogger, text="Starte GUI-Terminal",   command=self.but_terminalG,align="left")
            #self.buttLogOff.disable()             #self.buttLogOn.disable()
            self.txtLogger0   = "Logger On/Off Toggle - schalte den Logger ein oder aus"
            self.txtLogger1   = "SHELL Terminal - Befehle direkt an den Arduino"
            self.txtLogger2   = "GUI Terminal - Befehle direkt an den Arduino(Grafischer Oberfläche)"
            self.textLoggerB0 = Text(self.boxLogger, text=self.txtLogger0, align="top", size=10, width="fill")
            self.textLoggerB1 = Text(self.boxLogger, text=self.txtLogger1, align="top", size=10, width="fill")
            self.textLoggerB2 = Text(self.boxLogger, text=self.txtLogger2, align="top", size=10, width="fill")

            self.boxScan      = Box(self.app,width="fill",align="top",border=True)
            self.buttScan     = PushButton(self.boxScan, text="Alle Module anzeigen", command=self.but_scan_all, align="left")
            self.txtScan0     = "Starte den Monitor."
            self.txtScan1     = "ACHTUNG: Monitor aktualisiert sein Daten während wenn der Terminal aus ist!"
            self.txtScan2     = ""
            self.textScanB0   = Text(self.boxScan, text=self.txtScan0, align="top", size=10, width="fill")
            self.textScanB1   = Text(self.boxScan, text=self.txtScan1, align="top", size=10, width="fill")
            self.textScanB2   = Text(self.boxScan, text=self.txtScan2, align="top", size=10, width="fill")


            self.boxUeb       = Box(self.app,width="fill",align="top",border=True)
            self.buttUeb      = PushButton(self.boxUeb, text="Sende Mail mit Logs", command=self.but_uebersicht, align="left")
            self.txtUeb0     = "Sendet eine E-Mail mit den Log Daten der letzten X-Tage"
            self.txtUeb1     = "an:... <read from config>"
            self.txtUeb2     = "last send:... <read from config __cache> after being set by mail."
            self.textUebB0   = Text(self.boxUeb, text=self.txtUeb0, align="top", size=10, width="fill")
            self.textUebB1   = Text(self.boxUeb, text=self.txtUeb1, align="top", size=10, width="fill")
            self.textUebB2   = Text(self.boxUeb, text=self.txtUeb2, align="top", size=10, width="fill")

            self.boxDiagAll   = Box(self.app,width="fill",align="top",border=True)
            self.buttDiagAll  = PushButton(self.boxDiagAll, text="Diagramme erstellen", command=self.but_diagram_all, align="left")#, grid=[0,6])
            self.txtDiagA0     = "Erstelle Diagramme aller Module über die letzten zwei Tage"
            self.txtDiagA1     = "Erstellt für alle Module ein Diagramm in: ~/Desktop/Monitor/Bilder"
            self.txtDiagA2     = "ACHTUNG: Dieser Vorgang dauert ziemlich lange; je nach Modulzahl 10 Minuten ++"
            self.textDiagAB0   = Text(self.boxDiagAll, text=self.txtDiagA0, align="top", size=10, width="fill")
            self.textDiagAB1   = Text(self.boxDiagAll, text=self.txtDiagA1, align="top", size=10, width="fill")
            self.textDiagAB2   = Text(self.boxDiagAll, text=self.txtDiagA2, align="top", size=10, width="fill")

            self.boxAction    = Box(self.app,width="fill",align="bottom",border=True)
            self.textAction0  = Text(self.boxAction, text="Letzte Aktion: ", align="left", bg="white")
            self.textAction   = Text(self.boxAction, text=self.textStatus, align="left" )

            #self.debug_list['box_dbg_txt'].append(Text(self.boxActionDBG, text="CN2    : ", align="left", bg="white"))
            #self.debug_list['box_dbg_txt'].append(Text(self.boxActionDBG, text=self.textStatus, align="left" ))
            #self.debug_list['box_dbg_txt'].append(Text(self.boxActionDBG, text="Letzte Aktion: ", align="left", bg="white"))
            #self.debug_list['box_dbg_txt'].append(Text(self.boxActionDBG, text=self.textStatus, align="left" ))
            #self.debug_list['box_dbg_txt'].append(Text(self.boxActionDBG, text="Letzte Aktion: ", align="left", bg="white"))
            #self.debug_list['box_dbg_txt'].append(Text(self.boxActionDBG, text=self.textStatus, align="left" ))
            #self.debug_list['box_dbg_txt'].append(Text(self.boxActionDBG, text="Letzte Aktion: ", align="left", bg="white"))
            #self.debug_list['box_dbg_txt'].append(Text(self.boxActionDBG, text=self.textStatus, align="left" ))

            #self._debug_display = dict()
            #_settings= self._create_settings_dict()
            #self._debug_display = self._create_grouped_texts(self._debug_display, _settings)
            #def _create_grouped(self, lst, settings_dict):
            #    lst     = { 'box_h'     : ,
            #                'box_width' : 'fill',
            #                'box_align' : 'right',
            #                'box_border': True,
            #                'h_txt'     : list(),
            #                'h_align'   : list(),
            #                'h_bg'      : list(),
            #                }
#
#
            #        #lst     = { 'box_h'        : None,
            #        #           'box_width'     : 'fill',
            #        #           'box_align'     : 'right',
            #        #           'box_border'    : True,
            #        #           'txt_txt'       : list(),
            #        #           'txt_align'     : list(),
            #        #           'txt_bg'        : list(),
            #        #           }
            #_insert_to_box = {  'CN2:    ':'align=left,bg=white',
            #                    'CN4:    ':'align=left,bg=white',
            #                    'CN2_SER:':'align=left,bg=white',
            #                    'CN4_SER:':'align=left,bg=white',
            #                    'CN2_MON:':'align=left,bg=white',
            #                    'CN4_MON:':'align=left,bg=white',
            #                    'CN2_LOG:':'align=left,bg=white',
            #                    'CN4_LOG:':'align=left,bg=white'
            #                    }
            #def _create_settings_dict(self, insert_what:list, ):
            #    _bd = self.__base_dict()
            #    _box = Box(self.app,width="fill",align="bottom",border=True)
            #    _bd['']
#
            #def _cmp(self,stri,cmp='',fr=0,to='len_of_str',lower_str=True):
            #    _str    = stri if lower_str != True else stri.lower()
            #    _from   = fr
            #    _to     = to if (to != 'len_of_str') else len(str)
            #    _cmp    = cmp
            #    if (_str[_from:_to]==_cmp): return _cmp
            #    return False
#
            #def __base_dict(self):
            #    _lst     = {# box_handle and attributes
            #                'box_h'         : None,
            #                'box_width'     : None,
            #                'box_align'     : None,
            #                'box_border'    : None,
            #                }
            #    return _lst

            #'box_dbg': Box(self.app,width="fill",align="bottom",border=True),, 'box_dbg_txt' : list()
            #t_dict, b_width='fill',b_align='bottom', b_border=True,t_align='left',t_bg='white'

            #print(dir(_f))
            #exit()

            self.textLogger.repeat(1000,self.set_textLogger)
            self.set_textLogger()
            self.app.when_closed=self.exit_forcefully

            from hz_rr_monitor_direct02_b import mon_obj
            self.mon_obj = mon_obj
            self.mon_obj.__init__()

            from hz_rr_terminal import term_obj
            self.term_obj = term_obj
            self.term_obj.__init__()

            from hz_rr_terminalG import terg_obj
            self.terg_obj = terg_obj
            self.terg_obj.__init__()

            self.app.display()
            return 0
        finally:
            us.ser_obj.menu_run = 0

menu_obj = Menue()

if __name__ == "__main__":
    #us.ser_obj.ser_check()
    import usb_ser_b as us
    us.ser_obj.ser_check()

    #time.sleep(5)
    #us.ser_obj.run()
    menu_obj.draw_menue()
    #x = threading.Thread(target=menu_obj.draw_menue)
    #x.setDaemon(True)
    #x.start()

    #import hz_rr_monitor_direct02_b as md
    #y = threading.Thread(target=md.mon_obj.display_all())
    #y.setDaemon(True)
    #y.start()


    while True:
        pass




