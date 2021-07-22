#!/usr/bin/python3
# -*- coding: utf-8 -*-

import copy
import os
import platform
import stat
import subprocess
import threading
import time

import heizkreis_config as hkr_cfg
import hz_rr_config as cg
import hz_rr_debug as dbg
from guizero import App, Box, Combo, PushButton, Text
import usb_ser_b as us
import hr2_show_log03c as sl

if os.environ.get('DISPLAY','') == '':
    dbg.Debug().m('no display found. Using :0.0')
    os.environ.__setitem__('DISPLAY', ':0.0')
os.environ.__setitem__('DISPLAY', ':0')


global hkpar0
hkpar0=hkr_cfg.get_heizkreis_config(0)

filtFakt=hkpar0


#test
class Menue():
    heizkreis, modules, modTref, modSendTvor, dTLog, filtFakt = '','','','','',hkpar0

    boxTitle= textHeadline=boxTitle=  boxLogger=  textLogger= buttLogOn= buttLogOff= \
            txtLogger0= txtLogger1= txtLogger2= textLoggerB0= textLoggerB1= textLoggerB2= boxScan= \
            buttScan=   txtScan0=   txtScan1=   txtScan2=   textScanB0= textScanB1= textScanB2= \
            boxUeb=     buttUeb=    txtUeb0=    txtUeb1=    txtUeb2=    textScanB1= textScanB2= \
            textUebB0=  textUebB1=  textUebB2=  boxDiagAll= buttDiagAll= txtDiagA0= \
            txtDiagA1=  txtDiagA2=  textDiagAB0=textDiagAB1= textDiagAB2=boxAction= \
            textAction0=textAction= app = running_logger= running_monitor= None

    monitor_start = 0

    dbg = dbg.Debug(1)

    dbg.m(str(boxTitle))

    pltpath     =   cg.conf_obj.r ('system','logPlotPath')
    loggerpath  =   cg.conf_obj.r ('system','logStartScriptPath')
    lmdname     =   cg.conf_obj.r ('system','logMonitorDirectPath')

    def set_perm(self,f):
        try:
           # output = subprocess.check_output("sudo chmod u+rx " + f).decode("utf-8")
            self.dbg.m("chmod'", f, "'to", stat.S_IRWXU | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
            output = os.chmod(f, stat.S_IRWXU | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
            self.dbg.m(output)
        except Exception as e:
            self.dbg.m("error setting permissions for file ", f)
            self.dbg.m("error: ",e)
            #print("output: ", output)
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
        #print ( textlogger )
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
            us.ser_obj.block_log_until_TTL = 0
            us.ser_obj.logger_run = 1
            self.logger = True
            us.ser_obj.logger_pause = False
            self.dbg.m("thr_log_tog: LOGGER=ON",cdb=1)
        else:
            us.ser_obj.block_log_until_TTL = time.time()
            self.logger = False
            us.ser_obj.logger_pause = True
            us.ser_obj.logger_run = 0
            self.dbg.m("thr_log_tog: LOGGER=OFF",cdb=1)
        self.show_textLogger( self.logger )

    def runmon(self):
        completed = subprocess.run(
            ['hz_rr_monitor_direct02_b_start.sh'],#+" "+"startsilent"],
            shell=True,
            stdout=subprocess.PIPE,
        )
        time.sleep(0.5)
        #lmh.mon_obj.runme()
        #while self.mon_thread.is_alive():
        #    pass

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

    def but_terminal(self):
        #threading.Thread(target=self.__but_terminal).start()
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


    def thr_uebersicht(self):
        #self.textAction.value = "Erstelle Übersicht ..."
        #self.dbg.m(self.pltpath)
        #p = subprocess.Popen(
        #    [self.pltpath, 99],
        #    stdout = subprocess.PIPE,
        #    shell = True
        #)
        #for line in iter(p.stdout.readline, b""):
        #    self.textAction.value = line
        #self.textAction.value = "Erstelle Übersicht ... fertig"
        #time.sleep(1)
        self.textAction.value="---"
        self.dbg.ru()

    def but_uebersicht(self):
        threading.Thread(target=self.thr_uebersicht).start()

    def thr_diagram_all(self):
        self.textAction.value = "Erstelle Diagramme ..."
        pltpath=cg.conf_obj.r('system','logPlotPath')
        self.dbg.m(self.pltpath)
        sl.runme(99)
        #p = subprocess.Popen(
        #    [pltpath, '2', 'Z', 'F', '[]' ],
        #    stdout = subprocess.PIPE,
        #)
        #for line in iter(p.stdout.readline, b""):
        #    self.textAction.value = line
        self.textAction.value = "Erstelle Diagramme ... fertig"
        time.sleep(1)
        self.textAction.value="---"

    def but_diagram_all(self):
        threading.Thread(target=self.thr_diagram_all).start()

    def hotfixes(self):
        self.dbg.m("adding xhost +local:")
        self.run_cmd('xhost +local:')
        self.dbg.m("changing export MPLBACKEND=Agg")
        self.run_cmd("export MPLBACKEND='Agg'")
        self.dbg.m("done")
        self.dbg.m("[menue01.py] giving xauthority root permission")
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
            #global boxTitle, textHeadline, boxTitle, boxLogger, textLogger, buttLogOn, buttLogOff, \
            #        txtLogger0, txtLogger1, txtLogger2, textLoggerB0, textLoggerB1, textLoggerB2, boxScan, \
            #        buttScan, txtScan0, txtScan1, txtScan2, textScanB0, textScanB1, textScanB2, \
            #        boxUeb, buttUeb, txtUeb0, txtUeb1, txtUeb2, textScanB1, textScanB2, \
            #        textUebB0, textUebB1, textUebB2, boxDiagAll, buttDiagAll, txtDiagA0, \
            #        txtDiagA1, txtDiagA2, textDiagAB0, textDiagAB1, textDiagAB2, boxAction, \
            #        textAction0, textAction, app
            self.hotfixes()
            self.textStatus ="-***-"
            #app = App("HZ-RR Hauptmenü",layout="grid")
            self.app = App(title="HZ-RR Hauptmenü, Heizkreis %s"%(self.heizkreis),width=700,height=350)
            self.version = "1.0"
            self.hostname = cg.conf_obj.r('system', 'hostPath')

            if cg.conf_obj.islinux():
                fin = open(self.hostname,"r")
                self.hostname = fin.read().strip()
                fin.close()
            else:
                self.hostname = "WINDOWS"

            self.boxTitle     = Box(self.app,width="fill",align="top",border=True)
            self.textHeadline = Text(self.app, text="%s Menü Rücklauf-Reglung Version %s"%(self.hostname,self.version), align="top", width="fill")

            self.boxLogger    = Box(self.app,width="fill",align="top",border=True)
            self.textLogger   = Text(self.boxLogger, text="-", align="top", width="fill")
            self.buttLogTog   = PushButton(self.boxLogger, text="Logger on/off", command=self.but_log_tog, align="left")
            #self.buttLogOn.disable()
            self.buttTerminal = PushButton(self.boxLogger, text="Starte SHELL-Terminal", command=self.but_terminal,  align="left")
            #self.buttLogOff.disable()
            self.txtLogger0   ="Logger On/Off Toggle - schalte den Logger ein oder Aus"
            self.txtLogger1   ="Starte den Shell Terminal - sende Befehle direkt an den Arduino"
            self.txtLogger2   =""
            self.textLoggerB0 = Text(self.boxLogger, text=self.txtLogger0, align="top", size=10, width="fill")
            self.textLoggerB1 = Text(self.boxLogger, text=self.txtLogger1, align="top", size=10, width="fill")
            self.textLoggerB2 = Text(self.boxLogger, text=self.txtLogger2, align="top", size=10, width="fill")

            self.boxScan      = Box(self.app,width="fill",align="top",border=True)
            self.buttScan     = PushButton(self.boxScan, text="Alle Module anzeigen", command=self.but_scan_all, align="left")
            self.txtScan0     = "Starte den Monitor."
            self.txtScan1     = "ACHTUNG: Monitor aktualisiert sein Daten nur wenn der Terminal aus ist!"
            self.txtScan2     = ""
            self.textScanB0   = Text(self.boxScan, text=self.txtScan0, align="top", size=10, width="fill")
            self.textScanB1   = Text(self.boxScan, text=self.txtScan1, align="top", size=10, width="fill")
            self.textScanB2   = Text(self.boxScan, text=self.txtScan2, align="top", size=10, width="fill")

            self.boxUeb       = Box(self.app,width="fill",align="top",border=True)
            self.buttUeb      = PushButton(self.boxUeb, text="Übersicht erstellen", command=self.but_uebersicht, align="left")
            self.txtUeb0     = "Erstelle Uebersicht aller Module als .pdf Datei"
            self.txtUeb1     = "im Verzeichnis ~/Desktop/Monitor/Bilder"
            self.txtUeb2     = ""
            self.textUebB0   = Text(self.boxUeb, text=self.txtUeb0, align="top", size=10, width="fill")
            self.textUebB1   = Text(self.boxUeb, text=self.txtUeb1, align="top", size=10, width="fill")
            self.textUebB2   = Text(self.boxUeb, text=self.txtUeb2, align="top", size=10, width="fill")

            self.boxDiagAll   = Box(self.app,width="fill",align="top",border=True)
            self.buttDiagAll  = PushButton(self.boxDiagAll, text="Diagramme erstellen", command=self.but_diagram_all, align="left", grid=[0,6])
            self.txtDiagA0     = "Erstelle Diagramme aller Module über die letzten zwei Tage"
            self.txtDiagA1     = "Für jedes Modul wird eine .pdf Datei in ~/Desktop/Monitor/Bilder erstellt"
            self.txtDiagA2     = "ACHTUNG: Dieser Vorgang dauert ziemlich lange; je nach Modulzahl 10 Minuten ++"
            self.textDiagAB0   = Text(self.boxDiagAll, text=self.txtDiagA0, align="top", size=10, width="fill")
            self.textDiagAB1   = Text(self.boxDiagAll, text=self.txtDiagA1, align="top", size=10, width="fill")
            self.textDiagAB2   = Text(self.boxDiagAll, text=self.txtDiagA2, align="top", size=10, width="fill")

            self.boxAction    = Box(self.app,width="fill",align="bottom",border=True)
            self.textAction0  = Text(self.boxAction, text="Letzte Aktion: ", align="left", bg="white")
            self.textAction   = Text(self.boxAction, text=self.textStatus, align="left" )

            self.textLogger.repeat(1000,self.set_textLogger)
            self.set_textLogger()
            self.app.when_closed=self.exit_forcefully

            from hz_rr_monitor_direct02_b import mon_obj
            self.mon_obj = mon_obj
            self.mon_obj.__init__()

            from hz_rr_terminal import term_obj
            self.term_obj = term_obj
            self.term_obj.__init__()

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




