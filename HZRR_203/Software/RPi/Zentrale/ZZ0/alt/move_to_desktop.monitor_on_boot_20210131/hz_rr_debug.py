import inspect as it
import time as ti
import threading as th
import sys
import platform
import time
import hz_rr_config as cg


class Debug_Init:
    def __init__(self):
        #set values
        self.__DEBUG_CUSTOM_DBG_STATE_OVRWRT__           = int(cg.conf_obj.r('DEBUG-SETTINGS','custom_debug_state',          default = 0)) # > 0 activates
        self.__DEBUG_CUSTOM_DBG_SELECTIVE_DEBUG_OVRWRT__ = int(cg.conf_obj.r('DEBUG-SETTINGS','selective_debug_overwrite',   default = 0)) # > 0 activates [0/1]
        self.__DBG_LVL_VERBOSE                           = 10   # print 1-5
        self.__DBG_LVL_FUNCTIONS                         = 1    #
        self.__DBG_LVL_FUNCTIONS_AND_RETURN              = 2    #

class Debug(Debug_Init):

    linux = 0
    if platform.system() == "Linux": linux=1

    def __init__(self,d=1,m="[%s][%s][%s][%s]%s%s"):
        # lvl 1 - print
        # lvl 2 - write to log file
        self.logger_print_shortener     = bool(cg.conf_obj.r('DEBUG-SETTINGS',      'logger_print_shortener',           False))
        self.logger_print_shortener_maxl=  int(cg.conf_obj.r('DEBUG-SETTINGS',      'logger_print_shortener_max_l',     100))
        self.logger_print_shortener_frol= int(cg.conf_obj.r('DEBUG-SETTINGS',       'logger_print_shortener_from_left', 0))
        self.verbose_enable             = bool(cg.conf_obj.r('DEBUG-SETTINGS',      'verbose_log_enable',               False))
        self.verbose_path_linux         = cg.conf_obj.r('DEBUG-SETTINGS',           'verbose_log_linux',                '/media/pi/PYTHONUSB/move_to_desktop.monitor_on_boot/verbose/')
        self.verbose_path_win           = cg.conf_obj.r('DEBUG-SETTINGS',           'verbose_log_windows',              'D://coding//move_to_desktop.monitor_on_boot//rewrite//verbose')
        self.verbose_log_filemask       = cg.conf_obj.r('DEBUG-SETTINGS',           'verbose_log_filemask',             'VERBOSE_%Y-%m-%d_%H-%M-%S.dat')
        self.verbose_log_max_cdb        = int(cg.conf_obj.r('DEBUG-SETTINGS',       'verbose_log_max_cdb',              9))
        self.terminal_log_enabled       = bool(cg.conf_obj.r('MODULES',             'terminal_log_enabled',             True))
        self.nano_valve_log_a_enabled   = bool(cg.conf_obj.r('MODULES',             'nano_valve_log_a_enabled',         True))
        self.send_tvor_log_enabled      = bool(cg.conf_obj.r('MODULES',             'send_tvor_log_enabled',            True))
        self.exception_log_enabled      = bool(cg.conf_obj.r('MODULES',             'exception_error_log_enabled',      True))
        self.exception_log_name         = cg.conf_obj.r('module_log_settings',      'exception_log_name',               '_EXCEPTION_LOG.dat')
        self.tvor_log_name              = cg.conf_obj.r('module_log_settings',      'tvor_log_name',                    "_FAILED_TVOR_SENDS_LOG.dat")
        self.valve_assist_log_name      = cg.conf_obj.r('module_log_settings',      'valve_assist_log_name',            "_VALVE_ASSIST_LOG.dat")
        self.terminal_log_name          = cg.conf_obj.r('module_log_settings',      'terminal_log_name',                "_TERMINAL_LOG.dat")
        self.verbose_path               = self.verbose_path_win                                                 if not cg.conf_obj._tbl.islinux() else self.verbose_path_linux
        self.fname                      = self.verbose_path + "//" + time.strftime(self.verbose_log_filemask)   if not cg.conf_obj._tbl.islinux() else self.verbose_path + time.strftime(self.verbose_log_filemask)
        self.dbg_lvl                    = d
        self.dbg_str                    = m
        self.dbg_level_one_lines        = 75
        self.dbg_level_two_lines        = 80
        self.dbg_level_lever_dif        = 3
        self.__dbg_used_by              = { "MAINTHREAD":self.dbg_level_one_lines }
        self.__dbg_used_by_cnt          = 0
        self.__CONSTANTS                = Debug_Init()
        self.custom_debug_state         = 0 if( self.__CONSTANTS.__DEBUG_CUSTOM_DBG_STATE_OVRWRT__ == 0) else self.__CONSTANTS.__DEBUG_CUSTOM_DBG_STATE_OVRWRT__
        self.selective_debug_overwrite  = 0 if( self.__CONSTANTS.__DEBUG_CUSTOM_DBG_SELECTIVE_DEBUG_OVRWRT__ == 0) else self.__CONSTANTS.__DEBUG_CUSTOM_DBG_SELECTIVE_DEBUG_OVRWRT__ # this allows to only show level-debug created by custom state entries.
        self.__from_terminal            = False
        self.__mser_grab                = ""

    def get(self):
        x = self.__mser_grab
        #print("\n\n\n\n\n\n\nX:",x)
        self.__rst()
        return x[:-1]

    def __rst(self):
        self.__mser_grab = ""
        self.from_term(False)

    def add(self, x):
        if self.__from_terminal == True:
            self.__mser_grab += '>'+x + "\n"
            #print(self.__mser_grab)

    def from_term(self, v=True):
        if v != False:
            self.__from_terminal = True
        else:
            self.__from_terminal = False

    def const(self,n):
        #print(self.__CONSTANTS)
        #return getattr( self.__CONSTANTS, 'self.' + n )
        pass

    def ru(self):
        self.__remUser()

    def __remUser(self):
        #self.__dbg_used_by_cnt -= 1
        pass

    def __addUser(self, calling_thread=""):
        if calling_thread == "": return #print("error no thread") #error no thread..
        if calling_thread == "MAINTHREAD": return #print("mainthread - skip")#mainthread does not have to be added
        using_intend = self.dbg_level_two_lines# self.dbg_level_lever_dif*self.__dbg_used_by_cnt+self.dbg_level_two_lines
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
        return sys._getframe(1).f_back.f_back.f_code.co_name #str(it.stack()[1].f_back.f_back.f_code.co_name).upper()

    def debugToFile(self,text):
        pass

    def _slogs(self) -> bool:
        return self.logger_print_shortener

    def _sloglen(self) -> tuple():
        if (self.logger_print_shortener_frol != 0): self.logger_print_shortener_maxl += self.logger_print_shortener_frol
        return (self.logger_print_shortener_frol,self.logger_print_shortener_maxl)

    def _fw(self, _t:str, _name:str, _s='', _r='', _m="a", _encoding='utf-8') -> bool:
        try:
            _n = _name.replace(_s,_r) if (_s != '') else _name
            #print("_fw._n:",_n)
            n = open    ( _n, _m, encoding=_encoding )
            n.write     ( _t + "\n" )
            n.close     ()
            return True
        except Exception as e:
            print('exception',e)
        return False

    def _gm(self,_m, i = 0):
        while i < len(_m):
            if type(_m[i]) == None:           _m[i] = "(NoneType)"
            if type(_m[i]) == type(bool()):   _m[i] = "(True)" if (_m[i]) else "(False)"
            if type(_m[i]) != type("string"): _m[i] = str(_m[i])
            i += 1
        return _m

    def dbg_msg(self,m,cdb=0):
        call_fname          = self.callersFileName()        # + length formatting..
        call_thread         = self.callingThread()          #[MAINTHREAD] 60
        call_datenow        = self.callingTime()            #   [THREAD-x]  65
        call_functionname   = self.callingFunction()        #   cf #self.callingFunction()        #   [THREAD-y]  65
        custom_intend = self.__dbg_used_by.get(call_thread)
        if custom_intend == None:                           #print( "custom intend:",custom_intend,sep=" ", end= " ", flush=True )
            print("this should not have happend - taking default vlue")
            custom_intend = self.dbg_level_two_lines

        if cdb == 2:                        # custom debug state 3 means show spam aswell
            level = cdb
            pass

        l = len(self.dbg_str)-10 + len(call_datenow) + len(call_thread) + len(call_fname) + len(call_functionname)
        using_spacing= self.dbg_level_one_lines if (call_thread == "MAINTHREAD") else custom_intend#self.dbg_level_two_lines
        string_spacing = " "*(using_spacing-l) if (l < using_spacing) else ""
        x = self.dbg_str%(call_datenow, call_thread, call_fname, call_functionname, string_spacing, m)
        x = x.replace("\n",";")
        return x

    def m(self,*m, cdb=0):
        if cdb == -1:                   #   disable all messages
            return

        t = self.dbg_msg(" ".join(self._gm(list(m))))   # clean the string and convert all possible errors to string

        if self.__from_terminal:        #   print("self.__from_terminal:",self.__from_terminal)
            if (cdb > -4) and (cdb < 10):
                _m =" ".join(self._gm(list(m))).replace("\n",";")
                m = "[" + self.callingThread() + "] " + _m #print(m)
                self.add(m)             #   add to internal debug terminal queue
                if cdb == -4: return    #   only terminal print

        if (cdb == -7):                 #   special EXCEPTION_LOG log, to show where work has been done.
            if self.exception_log_enabled:
                self._fw( t, self.fname, '.dat', self.exception_log_name )

        if (cdb == -6):                 #   special SEND_TVOR log, to show where work has been done.
            if self.send_tvor_log_enabled:
                self._fw( t, self.fname, '.dat', self.tvor_log_name )

        if (cdb == -5):                 #   special VALVE_ASSIST log, to show where work has been done.
            if self.nano_valve_log_a_enabled:
                self._fw( t, self.fname, '.dat', self.  valve_assist_log_name )

        if (cdb == -4):                 #   special terminal log
            if self.terminal_log_enabled:
                self._fw( t, self.fname, '.dat', self.terminal_log_name )

        if ((self.verbose_enable==True) and (int(cdb) >= -3) and (int(cdb) < 9)):
            if (self.verbose_log_max_cdb >= int(cdb)): self._fw( t, self.fname )

        if cdb == -3: #enable VERBOSE logging but stop printing it to console
            return # this works because verbose logging is one step above

        if cdb == -2:                                    #   fallback print
            return print(m)

        if self._slogs():                               #   trim if logger_print_shortener = True
            _f, _t = self._sloglen()
            t = t[_f:_t]

        if (self.selective_debug_overwrite > 0):        #   if selective debug, only print correct debug statements!
            if (self.selective_debug_overwrite == cdb): #   we want only a certain level to be printed.
                return print (t)
            else:                                       #   we dont want to print as selective overwrite does not match custom debug state
                return                                  #   remember in this mode we want very specific debug

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
        dbg.from_term()
        dbg.m("testetetetetet","meh","das","soll","gehen")
        dbg.m(dbg.get())

    dbg = Debug(1)
    dbg.from_term()
    dbg.m("testuzkzukzuk zuk  zuk zukzukzukzukzukzuk zukzukzukzuk")
    dbg.m(dbg.get())
    call_test()



