
import inspect as it
import time as ti
import threading as th
import sys
import os 
import json 
import platform
import time

odat = ""

#y = "/media/pi/PYTHONUSB/move_to_desktop.monitor_on_boot/rewrite/verbose/"
#outFileName=y+time.strftime('%Y%m%d_%H%M%S_verbose_log.dat')
#odat = open(outFileName, 'w' )


class Debug():
    linux = 0
    if platform.system() == "Linux":
        linux=1

    def __init__(self,d=1,m="[%s][%s][%s][%s]%s%s"):
        # lvl 1 - print
        # lvl 2 - write to log file
        self.dbg_lvl = d
        self.dbg_str = m
        self.dbg_level_one_lines=65
        self.dbg_level_two_lines=70

    def callersFileName(self):
        frame = it.stack()[1]
        filename = frame[0].f_back.f_back.f_code.co_filename
        del frame
        if (self.linux == 1):
            return str(filename.split("/")[-1:]).replace('[','').replace(']','').replace("'",'').upper()
        return str(filename.split("\\")[-1:]).replace('[','').replace(']','').replace("'",'').upper()

    def callingThread(self):
        return th.currentThread().getName().upper()

    def callingTime(self):
        z = ti.strftime('%Y.%m.%d_%H:%M:%S')
        z = ti.strftime('%H:%M:%S')
        return z

    def callingFunction(self): 
    #    str(it.stack()[1].f_back.f_back.f_code.co_name).upper()
        return sys._getframe(1).f_back.f_back.f_code.co_name

    def dbg_msg(self,m):
        call_fname          = self.callersFileName()
        call_thread         = self.callingThread()
        call_datenow        = self.callingTime()
        call_functionname   = self.callingFunction() #cf #self.callingFunction()
        # + length formatting..
        #[MAINTHREAD] 60
        #   [THREAD-x]  65
        #   [THREAD-y]  65
        l = len(self.dbg_str)-10 + len(call_datenow) + len(call_thread) + len(call_fname) + len(call_functionname)
        using_spacing= self.dbg_level_one_lines if (call_thread == "MAINTHREAD") else self.dbg_level_two_lines
        string_spacing = " "*(using_spacing-l) if (l < using_spacing) else ""
        x = self.dbg_str%(call_datenow, call_thread, call_fname, call_functionname, string_spacing, m)
       # odat.writelines(x)
        return x

    def m(self,*m):
        t = type("string")
        i = 0
        m = list(m)
        while i < len(m):
            if type(m[i]) != t:
                m[i] = str(m[i])
            i += 1
        t = self.dbg_msg(" ".join(m))
        return  print(t)



if __name__ == "__main__":

    def call_test():
        dbg.m("testetetetetet","meh","das","soll","gehen")

    dbg = Debug(1)
    dbg.m("test")
    call_test()



