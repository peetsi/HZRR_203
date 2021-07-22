#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
hr2_net_status10_common.py

common routines and function definitions for the modules
"..._exec.py"  and "..._UI.py"

'''


import os
import ast
import time
import configparser
import curses        # for getch() check key input

import hz_rr_config as cg
hkr_cfg = cg.hkr_obj


# ******************************************
# global variables

# group is binary coded:
# 1   read values
# 2   write parameter related
# 4   regulator and valve related
# implemented: 0 if not in the menu  
hr2Menu = [
    # Nr,group, version, implemented, name, [regs], NOTE
    # NOTE group e {0,1,2,4,8,16,...} bin flags.
    # *** read data
    [ "1", 1, 1, 1, "ping", [0], ""],
    [ "2", 1, 1, 1, "read status values part 1", [0], ""],
    [ "4", 1, 1, 1, "read status values part 2", [0], ""],
    [ "5", 1, 1, 1, "read parameter: module / reg.part 1", [0], ""],
    [ "6", 1, 1, 1, "read parameter: reg.part 2", [0], ""],
    [ "7", 1, 1, 1, "read parameter: reg.part 3", [0], ""],
    [ "20", 2, 1, 1, "hex, send zentrale Vorlauftemperatur",[0], ""],
    [ "22", 2, 1, 1, "hex, send parameter for modul or regulator set 1", [0,1,2,3],"1,2,3 !!!tVlRxValid double!!!" ],
    [ "23", 2, 1, 1, "hex, send parameter for regulator set 2", [1,2,3], ""],
    [ "24", 2, 1, 1, "hex, send parameter for regulator set 3", [1,2,3], ""],
    [ "25", 2, 1, 1, "hex, send parameter for regulator set 4 - special parameters", [1,2,3], ""],

    [ "30", 2, 1, 1, "hex, reset parameters to factory settings", [0], "volatile in RAM; after boot from eeprom"],
    [ "31", 4, 1, 1, "hex, move valve time and direction", [1,2,3], ""],
    [ "34", 4, 1, 0, "hex, set valve back to normal control / stop service mode / stop motors ", [1,2,3], ""],
    [ "35", 4, 1, 0, "hex, set regulator to active / inactive", [1,2,3], ""],
    [ "36", 4, 1, 0, "hex, fast mode on / off", [0], ""],
    [ "37", 1, 1, 1, "hex, read ms-timer value", [0], ""],
    [ "38", 2, 1, 1, "hex, copy all parameters from EEPROM to RAM", [0], ""],
    [ "39", 2, 1, 1, "hex, write all parameters from RAM to EEPROM", [0], ""],
    [ "3A", 4, 1, 1, "hex, RESET using watchdog; wait 10sec", [0], ""],
    [ "3B", 4, 1, 0, "hex, clear eeprom", [0], "for test purposes; use factory settings on restart"],
    [ "3C", 4, 1, 0, "hex, check if motor connected", [1,2,3], "NOT IMLEMENTED IN Nano-FW rev. 1"],
    [ "3D", 4, 1, 0, "hex, open and close valve to store times needed", [1,2,3], "takes up to 100sec !!!"],
    [ "3E", 4, 1, 0, "hex, switch off current motor", [0], ""],
    [ "3F", 4, 1, 1, "hex, receive motor current", [0], ""],

    [ "40", 4, 1, 0, "hex, LCD-light on/off", [0], ""],
    [ "41", 1, 1, 1, "hex, get jumper settings for module address and settings", [0], ""],

    # Nr,group, version, implemented, name, [regs], NOTE
    [ "s1", 8, 1, 1, "rx status1, set VLtemp, rx status1", [0,1,2,3], ""],
    [ "s2", 8, 1, 1, "get ms-tic > reset WD -> 15sec -> get ms-tic", [0], ""],
    [ "s3", 8, 1, 1, "read all parameters to file", [0,1,2,3], ""],
    [ "s4", 8, 1, 1, "move motor and read current", [1,2,3], ""],
    [ "s5", 8, 1, 1, "check motors: open-close repeat and plot current", [1,2,3], ""],
    [ "s6", 8, 1, 1, "change parameter and verify", [0,1,2,3], ""],

    # Nr,group, version, implemented, name, [regs], NOTE
    [ "1",64, 1, 1, "read variables from modules", [], "" ],
    [ "2",64, 1, 1, "parameter handling", [], "" ],
    [ "3",64, 1, 1, "modue and valve commands", [], "" ],
    [ "4",64, 1, 1, "function sequences", [], "" ],
    ["88",64, 1, 1, "SELECT >>> modules, regs, command, repeat", [], "" ],
    ["99",64, 1, 1, "turn statistics on/off", [], ""],
    ["F0",64, 1, 1, "hex, UI <-> exec-task communication test", [], ""],
    ["st",64, 1, 1, "START performing command", [], ""],
]


class StatusUI:
    ''' status variable and functions for hr2-module dialog '''
    modules = []   # all modules available in the net
    regulators = [0,1,2,3]
    order = {   # imported from UI pipe/file
        "modules"    : [],  # selected modules for commands
        "regulators" : [],  # selected regulators for each selected module
        "command"    : "-", # command or sequence to be performed
        "repeat"     : 0,   # nr of repeats of the command or sequence
        "statistics" : True,# store statistic information on net traffic
    }
    reply = {   #  sent to UI from exec-task 
        # () not yet implemented
        "ack"   : 0,  # 0: no reaction, 1:accepted, 2:performed
        "busy"  : 0,  # >0 if busy, not ready for new command
        "msg"   : "-", # () message/error to be displayed
        "proc"  : "-", # () process in work
        "bar"   : 0,  # () status bar, 0 from 100
        "reset" : 0,  # >0 to reset communication
    }
    start = {
        "startOrder"  : False,
        "orderTime"   : 0.0,
        "orderTimeOld": 0.0,  # previous order time
        "confirmed"   : "-",
    }
    value = {
        "tvor"        : 60.0   # Vorlauf temperature
    }
    # 
    hostname = ""
    ts = ""
    # possible commands
    cmdsAll = []   # all possible commands to modules
    cmdsAllow = [] # all allowed/implemented commands to modules

    # file names = string  # used by UI = user interface, exec = execution task
    tempPath = "temp/"  # UI, exec
    parPath  = "parameter/"  # UI, exec
    fnSettings     = parPath+"UiSettings.ini"  # UI  store last settings fro new-start
    fnStatistic    = tempPath+"commTest_"+hostname+"_"+ts+".dat" #  exec; collect comm.statistics
    fos            = None  # exec; file descriptor for statistic data
    fnStatSumm     = fnStatistic.rstrip(".dat")+"_summ.dat" #  UI,exec; evaluated comm.statistics
    fnPipe2exec    = tempPath+"pipe2exec.dat"  # UI, exec
    fnPipeFromExec = tempPath+"pipeFromExec.dat"  # UI, exec
    fnParameterRx  = parPath+"par_"+hostname+"_"+ts+"RX.dat"  # exec

    cmdtimeout = 5.0  # sec waiting for response from exec-task


stu = StatusUI()  # status for communication with user interface


# *** common functions

def make_list(a):
    ''' make python-list from comma separated string, 
        e.g. "1,2 ,4,  12 "  -> [1,2,4,12]
        allowed is list with allowed numbers
    '''
    a1 = a.replace(" ","")   # remove blanks
    a2 = a1.replace("[","")  # remove brackets
    a3 = a2.replace("]","")
    a4="["+a3+"]"
    a5 = ast.literal_eval(a4) # make list
    return a5

def get_modules():
    antwort = hkr_cfg.get_heizkreis_config(0,1)
    return( antwort[1] )

def _get_hostname():
    f = open("/etc/hostname","r")
    hs = f.read()
    hostname = hs.strip()
    return hostname

def check_path(p):
    ''' check if path p exists, if not, make it '''
    if not os.path.exists(p):
        os.makedirs(p)

def init_status():
    stu.ts = time.strftime('%Y%m%d-%H%M%S',time.localtime())
    stu.hostname = _get_hostname()
    stu.modules = get_modules()
    stu.fnStatistic = stu.tempPath+"commTest_"+stu.hostname+"_"+stu.ts+".dat"
    stu.fnPipe2exec = stu.tempPath+"pipe2exec.dat"
    stu.fnPipeFromExec = stu.tempPath+"pipeFromExec.dat"
    stu.fnParameterRx = stu.parPath+"par_"+stu.hostname+"_"+stu.ts+"RX.dat"

def write_answer_file(mode):
    ''' mode==0: write a default answer-pipe/file
        otherwise write stu.reply data '''
    if mode == 0:
        # *** write empty answer file exec -> UI
        stu.reply["ack"]  = 0
        stu.reply["busy"] = 0
        stu.reply["msg"]  = "-"
        stu.reply["proc"] = "-"
        stu.reply["bar"]  = 0
        stu.reply["reset"]= 0
    
    config = configparser.ConfigParser(allow_no_value=True)
    config["reply"] = stu.reply
    with open(stu.fnPipeFromExec,"w") as configfile:
        config.write(configfile)

def init_common():
    ''' initialize variables and files for _exec and _ui'''
    init_status()
    check_path( stu.tempPath )
    check_path( stu.parPath )
    write_answer_file(0)






if __name__ == "__main__":
    pass
