
import inspect as it
import time as ti
import threading as th
import sys
import os
import json
import platform
import time
import hz_rr_config as cg


#global init
#global __DEBUG_CUSTOM_DBG_STATE_OVRWRT__, \
#    __DEBUG_CUSTOM_DBG_SELECTIVE_DEBUG_OVRWRT__, \
#        __DBG_LVL_VERBOSE, __DBG_LVL_FUNCTIONS, \
#            __DBG_LVL_FUNCTIONS_AND_RETURN

class Debug_Init:
    def __init__(self):
        #set values
        self.__DEBUG_CUSTOM_DBG_STATE_OVRWRT__           = int(cg.conf_obj.r('DEBUG-SETTINGS','custom_debug_state',          default = 0)) # > 0 activates
        self.__DEBUG_CUSTOM_DBG_SELECTIVE_DEBUG_OVRWRT__ = int(cg.conf_obj.r('DEBUG-SETTINGS','selective_debug_overwrite',   default = 0)) # > 0 activates [0/1]
        self.__DBG_LVL_VERBOSE = 10 # print 1-5
        self.__DBG_LVL_FUNCTIONS = 1
        self.__DBG_LVL_FUNCTIONS_AND_RETURN = 2

class Debug(Debug_Init):

    linux = 0
    if platform.system() == "Linux":
        linux=1

    def __init__(self,d=1,m="[%s][%s][%s][%s]%s%s"):
        # lvl 1 - print
        # lvl 2 - write to log file
        self.verbose_enable             = cg.conf_obj.r('DEBUG-SETTINGS', 'verbose_log_enable',     'False')
        self.verbose_path_linux         = cg.conf_obj.r('DEBUG-SETTINGS', 'verbose_log_linux',      '/media/pi/PYTHONUSB/move_to_desktop.monitor_on_boot/verbose/')
        self.verbose_path_win           = cg.conf_obj.r('DEBUG-SETTINGS', 'verbose_log_windows',    'D://coding//move_to_desktop.monitor_on_boot//rewrite//verbose')
        self.verbose_log_filemask       = cg.conf_obj.r('DEBUG-SETTINGS', 'verbose_log_filemask',   'VERBOSE_%Y-%m-%d_%H-%M-%S.dat')
        self.verbose_log_max_cdb        = cg.conf_obj.r('DEBUG-SETTINGS', 'verbose_log_max_cdb',    9)
        self.terminal_log_enabled       = cg.conf_obj.r('MODULES',        'terminal_log_enabled',   True)
        self.nano_valve_log_a_enabled   = cg.conf_obj.r('MODULES',       'nano_valve_log_a_enabled',True)

        self.verbose_path               = self.verbose_path_win
        self.fname                      = self.verbose_path + "//" + time.strftime(self.verbose_log_filemask)
        if self.linux == 1:
            self.verbose_path           = self.verbose_path_linux
            self.fname                  = self.verbose_path + time.strftime(self.verbose_log_filemask)

        self.dbg_lvl                    =   d
        self.dbg_str                    =   m
        self.dbg_level_one_lines        =   75
        self.dbg_level_two_lines        =   80
        self.dbg_level_lever_dif        =   3
        self.__dbg_used_by              =   { "MAINTHREAD":self.dbg_level_one_lines }
        self.__dbg_used_by_cnt          =   0
        self.__CONSTANTS                =   Debug_Init()
        self.custom_debug_state         =   0 if( self.__CONSTANTS.__DEBUG_CUSTOM_DBG_STATE_OVRWRT__ == 0) else self.__CONSTANTS.__DEBUG_CUSTOM_DBG_STATE_OVRWRT__
        self.selective_debug_overwrite  =   0 if( self.__CONSTANTS.__DEBUG_CUSTOM_DBG_SELECTIVE_DEBUG_OVRWRT__ == 0) else self.__CONSTANTS.__DEBUG_CUSTOM_DBG_SELECTIVE_DEBUG_OVRWRT__ # this allows to only show level-debug created by custom state entries.

    def const(self,n):
        #print(self.__CONSTANTS)
        #return getattr( self.__CONSTANTS, 'self.' + n )
        pass

    def ru(self):
        self.__remUser()

    def __remUser(self):
        self.__dbg_used_by_cnt -= 1

    def __addUser(self, calling_thread=""):
        if calling_thread == "": return #print("error no thread") #error no thread..
        if calling_thread == "MAINTHREAD": return #print("mainthread - skip")#mainthread does not have to be added
        using_intend = self.dbg_level_lever_dif*self.__dbg_used_by_cnt+self.dbg_level_two_lines
        if self.__dbg_used_by.get(calling_thread) != None: return #print("value already set:",self.__dbg_used_by)# already with value-  if thread value is not empty.           
        self.__dbg_used_by_cnt += 1
        #self.__dbg_used_by_cnt = th.active_count()
        self.__dbg_used_by[calling_thread]=using_intend
        return #print("added user!",self.__dbg_used_by)#,"-> new(", x[1],":",using_intend,")")

    def callersFileName(self):
        frame = it.stack()[1]
        filename = frame[0].f_back.f_back.f_code.co_filename
        del frame
        if (self.linux == 1):
            return str(filename.split("/")[-1:]).replace('[','').replace(']','').replace("'",'').upper()
        return str(filename.split("\\")[-1:]).replace('[','').replace(']','').replace("'",'').upper()

    def callingThread(self):
        x = th.currentThread().getName().upper()
        self.__addUser(x)
        return x

    def callingTime(self):
        z = ti.strftime('%Y.%m.%d_%H:%M:%S')
        z = ti.strftime('%H:%M:%S')
        return z

    def callingFunction(self): 
    #    str(it.stack()[1].f_back.f_back.f_code.co_name).upper()
        return sys._getframe(1).f_back.f_back.f_code.co_name

    def debugToFile(self,text):
        pass

    def dbg_msg(self,m,cdb=0):
        call_fname          = self.callersFileName()
        call_thread         = self.callingThread()
        call_datenow        = self.callingTime()
        call_functionname   = self.callingFunction() #cf #self.callingFunction()
        # + length formatting..
        #[MAINTHREAD] 60
        #   [THREAD-x]  65
        #   [THREAD-y]  65
        custom_intend = self.__dbg_used_by.get(call_thread)
        #print( "custom intend:",custom_intend,sep=" ", end= " ", flush=True )
        if custom_intend == None: 
            print("this should not have happend - taking default vlue")
            custom_intend = self.dbg_level_two_lines
        # custom debug state 3 means show spam aswell
        if cdb == 2: 
            level = cdb
            pass
        l = len(self.dbg_str)-10 + len(call_datenow) + len(call_thread) + len(call_fname) + len(call_functionname)
        using_spacing= self.dbg_level_one_lines if (call_thread == "MAINTHREAD") else custom_intend#self.dbg_level_two_lines
        string_spacing = " "*(using_spacing-l) if (l < using_spacing) else ""
        x = self.dbg_str%(call_datenow, call_thread, call_fname, call_functionname, string_spacing, m)
        return x

    def m(self,*m, cdb=0):

        if cdb == -1: #disable all messages
            return

        if cdb == -2: #fallback print
            return print(m)

        t = type("string")
        i = 0
        m = list(m)
        while i < len(m):
            if type(m[i]) != t:
                m[i] = str(m[i])
            i += 1
        t = self.dbg_msg(" ".join(m))

        if (cdb == -5): # special VALVE_ASSIST log, to show where work has been done.
            if not self.nano_valve_log_a_enabled: return
            try:
                n = open(self.fname.replace('.dat','._VALVE_ASSIST_LOG.dat'),"a",encoding='utf-8')
                n.write(t + "\n")
                n.close()
            except Exception as e:
                return self.dbg_msg("Exception:", str(e),cdb=1)


        if (cdb == -4): # special terminal log
            if not self.terminal_log_enabled: return
            try:
                n = open(self.fname.replace('.dat','._TERMINAL_LOG.dat'),"a",encoding='utf-8')
                n.write(t + "\n")
                n.close()
            except Exception as e:
                return self.dbg_msg("Exception:", str(e),cdb=1)

        if ((self.verbose_enable=='True') and (int(cdb) >= -3) and (int(cdb) < 9)):
            if (int(self.verbose_log_max_cdb) >= int(cdb)):
                try:    #dont verbose log spam.
                    n = open(self.fname,"a",encoding='utf-8')
                    n.write(t + "\n")
                    n.close()
                except Exception as e:
                    self.dbg_msg("Exception:", str(e),cdb=1)
            else:
                pass
       # odat.writelines(x)

        if cdb == -3: #enable VERBOSE logging but stop printing it to console
            return # this works because verbose logging is one step above

        # if selective debug, only print correct debug statements!
        if (self.selective_debug_overwrite > 0):
            #we want only a certain level to be printed.
            if (self.selective_debug_overwrite == cdb):
                #print
                return print (t)
            else:
                #we dont want to print as selective overwrite does not match custom debug state
                #remember in this mode we want very specific debug
                return

        if (cdb <= self.custom_debug_state):
            print(t)
            # usage for very verbose debugging.
            # set the global war to a value > 0 
            # does activate the specific debug messages.
            # with the call dbg.m("VERBOSE DEBUG", LEVEL =X )
            # you can group different functions with different
            # numbers.
            # for example if you have 1 functions.
            # you use dbg.m(xx, LEVEL=1) -> level = 1
            # for the first function. level = 2 for second and so on.
            # now - in this file (hz_rr_debug.py) you can change to 
            # debug only messages from the requested level
        else:
            pass
            #print("(self.custom_debug_state <= custom_debug_state)=false[",self.custom_debug_state,"/",cdb,"]")
            #print("skipped debug of:",m)


if __name__ == "__main__":

    def call_test():
        dbg.m("testetetetetet","meh","das","soll","gehen")

    dbg = Debug(1)
    dbg.m("test")
    call_test()



