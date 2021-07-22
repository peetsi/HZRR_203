#!/usr/bin/python3

import configparser
import inspect
import platform
import subprocess
import functools
import time
import numpy as np
#from varname import nameof

import hz_rr_terminal_defines as td


class Conf_toolbox:

    def __init__(self):
        self.initd              = 1
        self.cls                = 1
        self.hostname           = None
        self.hostnamepath       = None
        self.callers_local_vars = []
        self.err_exceptions     = {}
        self.e                  = err()
        self.hkr_param_one      = None
        self.hkr_param_one      = None

    def islinux(self):
        if platform.system() == "Linux":
            return True
        return False

    def _get_hostname(self):
        if self.hostname == None:
            __hstname = self.hostnamepath if self.islinux() else 'NOTDEF'
            if self.islinux():
                try:
                    fin = open(__hstname,"r")
                    __hstname   = fin.read().strip()
                    fin.close()
                except Exception as e:
                    self.e.s('_get_hostname',e)
                    print("Exception:",e)
                    return ( self.e.g()[0], self.e.g()[1] )
            else:
                __hstname       = "NOTDEF"
            _hostname=      self.hostname     = __hstname
            _hostname_msk=  self.hostname_msk = "%__HSTNAME__%"
            return (_hostname, _hostname_msk)
        return (self.hostname, self.hostname_msk)

    def addobj(self, _o, _v):
        _v = str(_v)
        #print("[ADDOBJ] ",end="")
        #print("property:",_o," value:",_v)
        self.__setattr__(_o,_v)

    def i(self,caller_name="",_cv=""):
        if caller_name == "": return
        callers_local_var = self.__addcallervar()
        self.addobj(caller_name, _cv)
        #print("callers_local_var:"+str(callers_local_var))
        #print( "VARNAME caller_name:")
        #print( [var_name for var_name, var_val in callers_local_var if var_val is caller_name] )
        ##exit(0)

    def __addcallervar(self):
        callers_local_var = inspect.currentframe().f_back.f_back.f_locals.items()
        self.callers_local_vars.append(callers_local_var)
        return callers_local_var

    def cls(self,v=1):
        return self._cls_after_init_(v)

    def _cls_after_init_(self,x = None):
        x = self.cls if self.cls != None else None
        if x != None:
            subprocess.Popen(["cls" if not self.islinux() else 'clear'], shell=True).communicate()

    def show(self,s="__eq__"):
        return str(eval('self.'+s))

    def show_all(self):
        #dir(str(self.__dict__.keys()+','+self.__dict__.values().split(',')))
        return 

    def gv(self,o="",f="",w=""):
        x = 'self.' +o +'.gv('+ f +'.'+ w +')'
        #x = ''
        #self.setattr(o+'.', inner1)

        _x = o+'.'+f if o != "" else f
        _s = _x + "."+w
        #print('_s:',_s)
        try:
            return eval(_s)
        except:
            print( 'WARNING: VAR(%s) not been found'%(_s) )
            return ""

    def __has_attr_and_callable(self, do:str):
        if (self.__has_attr(do) and self.__is_callable(do)): return True
        return False

    def __has_attr(self, do:str):
        return (hasattr(self, do))

    def __is_callable(self, do:str):
        return (callable(getattr(self, do)))

    # (attribute_or_function_name,  x[0]
    # ...,                          x[1:-3]
    # command,                      x[-3] [get,set,]
    # _trigger_new_command,         x[-2]
    # call                          x[-1]
    def do(self,x:tuple):
        _c = x[0]
        _s1 = x[-1] if (len(x) > 1)             else 0  # return function(0) or return attrb(1) default if called without param
        _s2 = x[-2] if (len(x) > 3)             else 0  # different command(0/anything)! default
        _s3 = x[-3] if (len(x) > 3)             else 0  # the command(str)
        do = f"get_{_c}" if (_s2 == _s3 == 0)   else f"{_s3}_{_c}"
        if (_s3 == 0): return self.__get(do,_s1)        # wants get
        if (_s3 == 1): return self.__set(do,_s1)        # wants set

    def __get(self,do,_s1):
        _co = self.__has_attr_and_callable(do) if (_s1==1) else self.__has_attr(do)
        if _co: return getattr(self, do);''#, print("success:",x)
        return False,''#, print("failed:",x)

    def __set(self,do):
        pass


class err:
    def __init__(self):
        self.all    = {}
        self.last   = ""
        self.now    = ""
        self.count  = 0

    def s(self, msg, err ):
        return self.__s(msg,err)

    def __s(self,m,e):
        self.last, self.now
        self.now = m,e
        self.all = self.all['['+str(self.count)+']' + m] = err
        self.count += 1

    def g(self,w=0):
        return self.__g(w)

    def __g(self,w=0):
        _r=""
        if w==1:   return self.all
        elif w==0: return self.now
        elif w==3: return self.last
        elif w < 0:
            if (w*-1) > self.count: raise ValueError('w is higher than count of total log attributes: w:' + str(w) + '// self.count:' + str(self.count))
            _r = self.all.keys()[(w*-1)]+','+self.all.items()[(w*-1)]
            if _r == "": raise ValueError('w not found:',w,' //type:',type(w),'//_r:',_r)
            return dict(_r for e in _r.split(','))
        else:
            print("error: __g called with the wrong argument:",w)
            raise ValueError('w seems not to be a integer number:',w,' //type:',type(w))

tb = Conf_toolbox()

# Class Decorators: Using Decorators with methods defined in a Class

#class class_integrity_checκ:
#    def __call__(self, *args, **kwargs):
#        pass
        #print("FUCKING TEST2")
        #self._decorated = self
        #print("args:   ", args)
        #print("kwargs: ", kwargs)
        #
        #if (not self.__isinit__()):
        #    print("error - please initialize")
        #if (self.obj_name==""):
        #    print("error - obj.name=''")
        #exit(0)
        #       def wrapper(self, *args, **kwargs):
        #           print("wrapper:",self, '*args', *args, '**kwargs',**kwargs)
        #           if (not self.__isinit__()):
        #               print("error - please initialize")
        #               exit(0)
        #               return #method(self.__del__)
        #           if (self.obj_name==""):
        #               print("error - obj.name=''")
        #               exit(0)
        #               return #method(self.__del__)
        #           result = func(self, *args, **kwargs)
        #           return result
        #       return wrapper
        #   return decorato


def try_except_handler(_func=None, *, rate=1):
    """Sleep given amount of seconds before calling the function"""
    def deco_try_except(func):
        @functools.wraps(func)
        def wrapper_ty_except(*args, **kwargs):
            x = "_err_"
            try:
                x = func(*args, **kwargs)
            except Exception as e:
                print("_TRY_EXCEPT_HANDLER ERROR:",e)
            print("test")
            return x
        return wrapper_ty_except

    if _func is None:
        return deco_try_except
    else:
        return deco_try_except(_func)

#def is_init_handler(_func=None, *, rate=1):
#    """Sleep given amount of seconds before calling the function"""
#    def deco_is_init(func):
#        @functools.wraps(func)
#        def wrapper_is_init(*args, **kwargs):
#
#            x = func(*args, **kwargs)
#        return wrapper_is_init
#
#    if _func is None:
#        return deco_is_init
#    else:
#        return deco_is_init(_func)
def repeat(_func=None, *, num_times=2):
    def decorator_repeat(func):
        @functools.wraps(func)
        def wrapper_repeat(*args, **kwargs):
            for _ in range(num_times):
                value = func(*args, **kwargs)
            return value
        return wrapper_repeat

    if _func is None:
        return decorator_repeat
    else:
        return decorator_repeat(_func)

def count_calls(func):
    @functools.wraps(func)
    def wrapper_count_calls(*args, **kwargs):
        wrapper_count_calls.num_calls += 1
        print(f"Call {wrapper_count_calls.num_calls} of {func.__name__!r}")
        return func(*args, **kwargs)
    wrapper_count_calls.num_calls = 0
    return wrapper_count_calls

def is_init_handler(cls):
    """Make a class a Singleton class (only one instance)"""
    @functools.wraps(cls)
    def wrapper_init(*args, **kwargs):
        #def 
        pass

    #    if not wrapper_init.instance:
    #        wrapper_init.instance = cls(*args, **kwargs)
    #    return wrapper_init.instance
    #wrapper_init.instance = None
    #return wrapper_init


#@class_deco
class Conf(object):
    def __init__(self,using_conf="",_hkr=0,_term=0,_cv=""):
        print("__INIT__")
        if using_conf != "":
            #assigns None or "" or 0
            self.heizkreis=self.modules=self.modTRef=self.modSendTvor=self.dtLog=self.filtFakt=self.regActive=\
                self.TVorlAendWarn=self.TVorlAendAlarm=self.TRueckAendWarn=self.TRueckAendAlarm=self.TRueckDeltaPlus=self.TRueckDeltaMinus=\
                    self.venTravelWarn=self.venTravelAlarm=self.term_is_build=self.hostname=None
            self.obj        = ""
            self.initd      = 0
            self.hkrinitd   = 0
            self.obj_name   = ""
            self.obj_adr    = ""
            self.using_conf = ""
            self.caller_name= ""
            self.error_exit = ""
            self.name       = ""
            self.cmd        = ""
            self.cmd_e      = ""
            self.cmd_all    = ""
            #assigns with value
            self._rm        = ('[',']','"',"'")
            self.term_call  = True if (_term != 0)  else False
            self.hkr_call   = True if (_hkr != 0)   else False
            self.help       = td.hz_rr_Terminal_defines()
            self._tbl       = tb
            self.is_linux   = self._tbl.islinux()
            self.islinux    = self._tbl.islinux()
            #self.hkr        = _hkr
            self.caller_name= _cv
            #initialisee
            self._tbl.i     (using_conf,_cv)
            self.i          (using_conf,_cv)
            #decorating - fall back decorators
            #self.w                     = class_integrity_check()(self.w                    )#(self))
            #self.rs                    = class_integrity_check()(self.rs                   )#(self, section="", default="DEFAULT_ERR"))
            #self.ra                    = class_integrity_check()(self.ra                   )#(self, default="DEFAULT_ERR"))
            #self.buffer_ini_to_toolbox = class_integrity_check()(self.buffer_ini_to_toolbox)#(self))
            #self.reload                = class_integrity_check()(self.reload               )#(self))
            #self.r                     = class_integrity_check()(self.r                    )#(self, section, key, default="DEFAULT_ERR"))
            #self._add_to_tbl           = class_integrity_check()(self._add_to_tbl          )#(self, _o, _v))
            #onstart (complexer inits)
            self.__start__  ()
        else:
            _s = "__INIT__:"
            using_conf = "<empty>"
            self.error_exit=ValueError(f'{_s}using_conf not called with a valid ini file\nValueError: {_s}Ini file used:'+str(using_conf))
            raise self.error_exit

    def __del__(self):
        _v = str(self.error_exit).replace("ValueError: ",'').replace('\n',';').replace('__INIT__:','')
        if _v != "":
            print(f"__del__: ERROR Occured:\n       ({_v})")
        else:
            _v = eval('type(self)')
            _s = " "*22
            print(f"__del__: destructing (\n{_s}class:\t{_v}\n{_s}var:\t{self.caller_name}\n{_s}conf:\t{self.using_conf}\n{_s})")
        del self

    def __start__(self):
        if not self.__isinit__(): return print("error - please initialize")
        print("__start__")
        # add self
        self.obj_adr    = self         #print("__init__:", self.obj_name, "/", self.obj_adr)
        self.obj_name   = self._mrep(str(str(self.using_conf.split('/')[-1:]).split('.')[:-1]),self._rm) if self._tbl.islinux() else \
                            self._mrep(str(str(self.using_conf.split('\\')[-1:]).split('.')[:-1]),self._rm)
        self._add_to_tbl(self.obj_name, self.obj_adr)

        #build terminal config
        if (self.term_call != 0):
            if not self.term_is_build:
                self._build_terminal_db()
                self._set_term_is_build(True)

        # get heizkreis config (and self.heizkreis == None)??
        if (self.hkr_call != 0):
            self.ghc()

        # preload vars from config_ini
        if (self.term_call == 0 and self.hkr_call == 0):
            self.hostname = self.r('system','hostPath',         'NOTDEF')
            self.setonusb = self.r("system","conf_set_on_usb",  1)
            self.confpath = self.r("system","confPath_local_linux") if self._tbl.islinux() else self.r("system","confPath_local_win")
            if (self.setonusb == 1):
                self.confpath= self.r("system","confPath_USB_linux") if self._tbl.islinux() else self.r("system","confPath_USB_win")

        #read all
        #buffer ini in object
        self.buffer_ini_to_toolbox()

    def i(self,n,c):
        self.using_conf  = n
        self.caller_name = c
        try:
            self.obj         = configparser.ConfigParser()
            _d               = self.obj.read(self.using_conf)
        except Exception as e:
            return
            raise print("Conf __INIT__ Error:",e)
        print(_d)
        self.initd       = 1
        #print("self.obj.read:",_d)
        #try:
        #except Exception as e:
        #    raise Exception(e)

    def __pre_checks(self):
        pass

    def _mrep(self,s:str,w:tuple,wi=('',)):
        if (len(wi)==1 and wi[0]==''): w = dict(zip(w, ['' for _x in w]))
        for _x in w: s = s.replace(_x,w[_x])
        return s
        #exec("""def {name}():
        #  print '{name}'
        #""".format(name='any')) in globals()
        #
        #any()  # prints 'any'

    #@class_integrity_checκ()()
    def _add_to_tbl(self, _o, _v):
        self._tbl.addobj(_o, _v)

    #@class_integrity_checκ()
    def r(self, section, key, default="DEFAULT_ERR"):
        if not self.__isinit__(): return print("error - please initialize")
        ##if (self.obj_name==""): return   print("error - obj.name=''")
        _l = "."#".__"
        _r = "."#"__."
        _x = self.obj.get(section, key, fallback=default, raw=True)
        if (_x == 'True' or _x == 'False'): _x = True if (_x == 'True') else False
        self.__setattr__(section+_r+key,_x)
        self._add_to_tbl(self.obj_name+_l+section+_r+key, _x)
        return _x

    #@class_integrity_checκ()
    def reload(self):
        x = self.buffer_ini_to_toolbox()
        return x

    #@class_integrity_checκ()
    def buffer_ini_to_toolbox(self):
        if not self.__isinit__(): return print("error - please initialize")
        #if (self.obj_name==""): return   print("error - obj.name=''")
        if not (self.hkr_call == 1 or self.term_call == 1): self._tbl.hostnamepath = self.hostname
        rval = {}
        x = self.ra()
        for w in x:
            b = self.rs(w)
            for v in b:
                rval[str(w)] = str(v)
                ste = 'self._tbl.'+str(w) +'.'+ str(v) + " = '" + str(b[v] +"'")
                #print(ste)
                #exec(ste)
        return

    #@class_integrity_checκ()
    def ra(self, default="DEFAULT_ERR"):
        if not self.__isinit__(): return print("error - please initialize")
        #if (self.obj_name==""): return   print("error - obj.name=''")
        _l = "."#".__"
        _r = ""#"__."
        _x = self.obj.sections()
        for w in _x:
            self._add_to_tbl(self.obj_name+_l+w+_r, w)
            self.__setattr__(w,w)
        return _x

    #@class_integrity_checκ()
    def rs(self, section="", default="DEFAULT_ERR"):
        if not self.__isinit__(): return print("error - please initialize")
        #if (self.obj_name==""): return   print("error - obj.name=''")
        _l = "."#".__"8
        _r = "."#"__."
        _x = dict(self.obj.items(section, raw=True))#
        #print("SECT:",section)
        #print("DICT:",_x)
        for w,v in _x.items():
            self._add_to_tbl(self.obj_name+_l+section+_r+w, v)
            self.__setattr__(section+_r+w,v)
        return _x

    #@class_integrity_checκ()
    def w(self):
        if not self.__isinit__(): return print("error - please initialize")
        #if (self.obj_name==""): return   print("error - obj.name=''")
        with open(self.using_conf, 'w') as configfile:
            self.obj.write(configfile)

    def __isinit__(self):
        if self.initd: return True
        return False

    def _termminal_is_build(self):
        if self.term_is_build == True: return True
        return False

    def _set_term_is_build(self,v=True):
        self.term_is_build = False
        if v==True: self.term_is_build = True

    def gtb(self):
        return self._get_term_build()

    def _get_term_build(self):
        v = ( self.name, self.cmd, self.cmd_e, self.cmd_all )
        return v

    def _build_terminal_db(self):
        if not self.term_call: return print( "warning: this can only be called from terminal config obj.")
        self.__GLOBAL_SETTING_str  = '__GLOBAL_SETTINGS__'
        self.desc_new               = ''
        self.cmd_e                  = {}
        self.cmd                    = []
        self.cmd_all                = []
        _prsu                       = ( '%__', '__%')
        _rm                         = { 'name': _prsu[0] + 'NAME' + _prsu [1],  'call': _prsu[0] + 'CALL' + _prsu [1],
                                        'retv': _prsu[0] + 'RETV' + _prsu [1],  'desc': _prsu[0] + 'DESC' + _prsu [1] }
        _ra = self.ra()
        for x in _ra:
            _def_cmask                  =  _rm['name']+','+_rm['call']
            _def_dmask                  =  _rm['name']+"\n\n "+_rm['call']+"\n\n "+_rm['desc']+"\n\n "+_rm['retv']
            _def_slaw                   =   5
            self.cmask                  = str(self.r(self.__GLOBAL_SETTING_str, 'cmask', _def_cmask))
            self.dmask                  = str(self.r(self.__GLOBAL_SETTING_str, 'dmask', _def_dmask))
            self.split_lines_after_words= int(self.r(self.__GLOBAL_SETTING_str, 'split_lines_after_words', _def_slaw))
            __debug_lvl = 3
            #print("_def_cmask : self.cmask ('%s':'%s')"%(_def_cmask,self.cmask))
            #print("_def_dmask : self.dmask ('%s':'%s')"%(_def_dmask,self.dmask))
            #print("_def_slaw : self.split_lines_after_words ('%s':'%s')"%(str(_def_slaw), str(self.split_lines_after_words)))
            t = self.rs(x)
            if x!=self.__GLOBAL_SETTING_str:
                _ga = ""
                self.name   = x            #   read_stat
                self.retv   = t ['retv'].replace('\\n','\n')    #   <text>
                self.call   = t ['call'].replace('\\n','\n')       #   int,int
                self.cmask  = self.cmask.replace(_rm['name'],self.name).replace(_rm['call'],self.call)
                self.cmd.append(self.cmask)
                self.call_new= ""
                _tx = self.call+","
                _tm = self.call.split(',') if (self.call.find(',') > 0 ) else _tx.split(',')
                for args in _tm:
                    alo = args.lower()
                    if alo == 'int':    self.call_new += alo + '= requires a number without decimal place' +"\n"
                    if alo == 'float':  self.call_new += alo + '= requires a decimal number'               +"\n"
                    if alo == 'str':    self.call_new += alo + '= requires a string (text) (abcde..)'      +"\n"
                self.desc = t['desc']
                _desc = self.desc.split(" ")   #   <text> - parse and set \n every 5 words cause of small resolution on rasp
                if len(self.desc) > 5:
                    c=0
                    for words in _desc:
                        if ((c+1)%self.split_lines_after_words) == 0: # rest after divison = 0
                            _desc[c] += "\n"
                        c+=1
                self.desc_new = ""
                for _w in _desc:
                    self.desc_new += _w + " "
                self.desc_new = self.desc_new[:-1]
                _kwn = { _rm['name']:x, _rm['call']:self.call_new, _rm['desc']:self.desc_new, _rm['retv']:self.retv }
                for entry in _kwn:
                    self.dmask =  self.dmask.replace( entry ,_kwn[entry] ).replace('\\n','\n')
                    pass
                _ga = self.name+";"+self.call+";"+self.retv+";"+self.desc
                self.cmd_all.append( _ga )
                h = self.help.r(self.name+','+self.call, self.cmask, self.dmask)
                self.cmd_e[x]=h
        print("terminal build done - can be retrieved now")

    def _get_hostname(self):
        if not self.__isinit__():   return print("error - please initialize")
        self.hostname = self._tbl.hostname if (self._tbl.hostname != None) else "NOTDEF"
        return self._tbl.hostname if (self._tbl.hostname != None) else "NOTDEF"

    def get_heizkreis_config( self, parameter = 0, readfromusb = 1 ):
        if (self.hkr_call == False):    return print("warning - this object is not the heizkreis config")
        if not self.__isinit__():       return print("error - please initialize")
        if not self.hkr_call:           return print("warning - get_heizkreis_config has been called while self.hkr == 0")
        if (parameter == 0):
            _r = (self.heizkreis, self.modules, self.modTRef, self.modSendTvor, self.dtLog, self.filtFakt)
            self._tbl.hkr_param_one = _r
            return _r
        elif (parameter == 1):
            _r = (self.regActive,self.TVorlAendWarn,self.TVorlAendAlarm,\
                        self.TRueckAendWarn,    self.TRueckAendAlarm,\
                        self.TRueckDeltaPlus,   self.TRueckDeltaMinus,\
                        self.venTravelWarn,     self.venTravelAlarm)
            self._tbl.hkr_param_two = _r
            return _r

    def ghc(self):
        if not self.hkr_call:           return print("warning - this object is not the heizkreis config")
        print("GHC CALLED")
        self._get_heizkreis_config(0,1)
        self._get_heizkreis_config(1,1)
        self.hkrinitd=1

    def _get_heizkreis_config( self, parameter = 0, readfromusb = 1 ):
        if not self.hkr_call:            return False, print("warning - get_heizkreis_config has been called while self.hkr == 0")
        _x = self._tbl._get_hostname()[0]
        print("_get_heizkreis_config:", _x, "==", _x)
        print("[LOADING HEIZKREIS CONFIG]\nusing HKR conf:",_x)
        fhk = self.rs(_x)
        err = 0
        try:
            # Nr. des Heizkreises
            #heizkreis = int([hkline for hkline in hks if "heizkreis" in hkline][0].split()[1])
            self.heizkreis = int(fhk['heizkreis'])
            print("heizkreis=",self.heizkreis)
        except Exception as e:
            err = 2

        try:
            # Nummern einzulesender Module
            #m = [ hkline for hkline in hks if "modules" in hkline][0].split()[1]
            m = fhk['modules']
            print("modules=",m)
            self.modules = np.array( m.split(","), int )
            print("modules=",self.modules)
        except Exception as e:
            err = 3

        try:
            # Modul mit zentraler Vorlauftemperatur; 0 falls es fehlt
            #modTRef = int([hkline for hkline in hks if "Modul_Tvor" in hkline][0].split()[1])
            self.modTRef = int(fhk['Modul_Tvor'.lower()])
            print("(Modul_Tvor)modTRef=",self.modTRef)
        except Exception as e:
            err = 4

        try:
            # Module an welche zentrale Vorlauftemperaturen gesendet werden
            #m = [ hkline for hkline in hks if "modSendTvor" in hkline][0].split()[1]
            m = fhk['modSendTvor'.lower()]
            print("modSendTvor=",m)
            self.modSendTvor = np.array( m.split(","), int )
            print("modSendTvor=",self.modSendTvor)
        except Exception as e:
            err = 5

        try:
            # Intervall zum Abruf der Daten von den Modulen in Sekunden:
            #dtLog = int([hkline for hkline in hks if "interval" in hkline][0].split()[1])
            self.dtLog = int(fhk['interval'.lower()])
            print("dtLog=",self.dtLog)
        except Exception as e:
            err = 6

        try:
            # Filter faktor zur Bewertung der neuen Messwertes zentrale Vorlauftemperatur
            #filtFakt = float([hkline for hkline in hks if "filterfaktor" in hkline][0].split()[1])
            self.filtFakt = float(fhk['filterfaktor'.lower()])
            print("filtFakt=",self.filtFakt)
        except Exception as e:
            err = 7

        if parameter == 1 :
            pass
            try:
                # Anzahl aktiver Regler in jedem Modul
                #m = [ hkline for hkline in hks if "regActive" in hkline][0].split()[1]
                m = fhk['regActive'.lower()]
                print("regActive=",m)
                self.regActive = np.array( m.split(","), int )
                print("regActive=",self.regActive)
            except Exception as e:
                print(e)
                err = 8

            try:
                #  Aenderung in der Temperatur von Vorlauf/Stunde:
                #TVorlAendWarn = float([hkline for hkline in hks if "TVorlAendWarn" in hkline][0].split()[1])
                self.TVorlAendWarn = float(fhk['TVorlAendWarn'.lower()])
                print("TVorlAendWarn=",self.TVorlAendWarn)
            except Exception as e:
                err = 9

            try:
                #TVorlAendAlarm = float([hkline for hkline in hks if "TVorlAendAlarm" in hkline][0].split()[1])
                self.TVorlAendAlarm = float(fhk['TVorlAendAlarm'.lower()])
                print("TVorlAendAlarm=",self.TVorlAendAlarm)
            except Exception as e:
                err = 10

            try:
                #  Aenderung in der Temperatur von Ruecklauf/Stunde:
                #TRueckAendWarn = float([hkline for hkline in hks if "TRueckAendWarn" in hkline][0].split()[1])
                self.TRueckAendWarn = float(fhk['TRueckAendWarn'.lower()])
                print("TRueckAendWarn=",self.TRueckAendWarn)
            except Exception as e:
                err = 11

            try:
                #
                #TRueckAendAlarm = float([hkline for hkline in hks if "TRueckAendAlarm" in hkline][0].split()[1])
                self.TRueckAendAlarm = float(fhk['TRueckAendAlarm'.lower()])
                print("TRueckAendAlarm=",self.TRueckAendAlarm)
            except Exception as e:
                err = 12

            try:
                #
                #TRueckDeltaPlus = float([hkline for hkline in hks if "TRueckDeltaPlus" in hkline][0].split()[1])
                self.TRueckDeltaPlus = float(fhk['TRueckDeltaPlus'.lower()])
                print("TRueckDeltaPlus=",self.TRueckDeltaPlus)
            except Exception as e:
                err = 13

            try:
                #
                #TRueckDeltaMinus = float([hkline for hkline in hks if "TRueckDeltaMinus" in hkline][0].split()[1])
                self.TRueckDeltaMinus = float(fhk['TRueckDeltaMinus'.lower()])
                print("TRueckDeltaMinus=",self.TRueckDeltaMinus)
            except Exception as e:
                err = 14

            try:
                #
                #venTravelWarn = float([hkline for hkline in hks if "venTravelWarn" in hkline][0].split()[1])
                self.venTravelWarn = float(fhk['venTravelWarn'.lower()])
                print("venTravelWarn=",self.venTravelWarn)
            except Exception as e:
                err = 15

            try:
                #
                #venTravelAlarm = float([hkline for hkline in hks if "venTravelAlarm" in hkline][0].split()[1])
                self.venTravelAlarm = float(fhk['venTravelAlarm'.lower()])
                print("venTravelAlarm=",self.venTravelAlarm)
            except Exception as e:
                err = 16

        print("done reading all: (heizkreis=", self.heizkreis, ")")

        if err > 0:
            return(["err",err])
        else:
            if parameter == 0:
                rv0=(self.heizkreis, self.modules, self.modTRef, self.modSendTvor, self.dtLog, self.filtFakt)
                return rv0
            if parameter == 1:
                rv1=(self.regActive,self.TVorlAendWarn,self.TVorlAendAlarm,\
                    self.TRueckAendWarn,    self.TRueckAendAlarm,\
                    self.TRueckDeltaPlus,   self.TRueckDeltaMinus,\
                    self.venTravelWarn,     self.venTravelAlarm)
                return rv1

#t = Conf()     # raises exception as wanted.
#t.r('','','')
#print("t:",t)
configfile_n                = "config\hz_rr_config.ini"           if (not tb.islinux()) else "/media/pi/PYTHONUSB/move_to_desktop.monitor_on_boot/config/hz_rr_config.ini"
hkr_config                  = "config\heizkreis.ini"              if (not tb.islinux()) else "/media/pi/PYTHONUSB/move_to_desktop.monitor_on_boot/config/heizkreis.ini"
terminal_defines_config     = "config\hz_rr_terminal_defines.ini" if (not tb.islinux()) else "/media/pi/PYTHONUSB/move_to_desktop.monitor_on_boot/config/hz_rr_terminal_defines.ini"
gui_terminal_config         = "config\hz_rr_gui_terminal.ini"     if (not tb.islinux()) else "/media/pi/PYTHONUSB/move_to_desktop.monitor_on_boot/config/hz_rr_gui_terminal.ini"
conf_obj                    = Conf(configfile_n,                    _cv="c")
hkr_obj                     = Conf(hkr_config,              _hkr=1, _cv="h")
terc_obj                    = Conf(terminal_defines_config, _term=1,_cv="t")
terg_obj                    = Conf(gui_terminal_config,             _cv='g' )
#
#a = 0
#id_a = id(a)
#print(id_a)
#the_variable =var_id =None
#variables = {**locals(), **globals()}
#for var in variables:
#    exec('var_id=id(%s)'%var)
#    if var_id == id_a:
#        exec('the_variable=%s'%var)
#print(the_variable)
#print(id(the_variable))
#print("a:",globals())
#print("b:",*globals())
#print("c:")
#_x ={**globals()}
#print(str(_x))
if __name__ == "__main__":
    s = 5
    if s == -1:
        pass



    elif s==0:
        print(tb.gv('hz_rr_config','system','serialPort_PIfour'))
        print(tb.gv('','system','serialPort_PIfour'))
        print(tb.show_all())
        print("EMPTY")
        #print(conf_obj.__dict__.items())
        print("conf_obj:"+str(dir(conf_obj)))
        #print(conf_obj.system.confpath_local_win)
        #print(dir(tb))
        #print(conf_obj)
        #print(1+"")            # let programm exception, for debug reason

    elif s==1:
        _s = "system"
        _h = "hostPath"
        _n = 'NOTDEF'
        _a = tb.hz_rr_ceonfig.r          (_s, _h, _n)
        _b = tb.hz_rr_terminal_defines.r(_s, _h, _n)
        _c = tb.heizkreis.r             (_s, _h, _n)
        print ("_a:",_a)
        print ("_b:",_b)
        print ("_c:",_c)
        _aa = conf_obj._tbl.  _get_hostname(_a)
        _bb = hkr_obj._tbl.   _get_hostname(_b)
        _cc = terc_obj._tbl.  _get_hostname(_c)
        print ("_aa:",_aa)
        print ("_bb:",_bb)
        print ("_cc:",_cc)

    elif s==2:
        _conf = tb.hz_rr_config
        print(_conf.hostname)

        print("tb.__dict__.keys():",    str(tb.__dict__.keys())[:100])
        print("conf_obj._tbl.keys():",  str(conf_obj._tbl.__dict__.keys())[:100])
        print("hkr_obj._tbl.keys():",   str(hkr_obj._tbl.__dict__.keys())[:100])
        print("terc_obj._tbl.keys():",  str(terc_obj._tbl.__dict__.keys())[:100])

        print("id_tb:",         id(tb))
        print("id_conf_obj:",   id(conf_obj._tbl))
        print("hkr_obj:",       id(hkr_obj._tbl))
        #tb._cls_after_init_()
        print("terc_obj:",      id(terc_obj._tbl))

    elif s==3:
        r = conf_obj.r('system', 'serialPort_WIN')
        print(r)
        r = conf_obj.r('system', 'serialPort_PIthree')
        print(r)
        r = conf_obj.r('system', 'serialPort_PIfour')
        print(r)
        r = hkr_obj.ra()
        print(r)
        hn = conf_obj.r('system','hostPath') if conf_obj._tbl.islinux() else 'NOTDEF'
        r = hkr_obj.rs('ZZ3HR2')
        print(r)
        r = r['modul_tvor']
        print(r)
        r = hkr_obj.r('ZZ3HR2', 'modul_tvor')
        print(r)
        r = terc_obj.ra()
        print(r)
    elif s==4:
        c=1
        __GLOBAL_SETTING_str = '__GLOBBAL_SETTING'
        h = terc_obj.r(__GLOBAL_SETTING_str, 'mask', "%__NAME__%\n\n %__CALL__%\n\n %__DESC__%")
        print("[%s] mask:"%(__GLOBAL_SETTING_str),h)
        for x in r:
            t = terc_obj.rs(x)
            print("[%s]"%(x))
            if x!=__GLOBAL_SETTING_str:
                s1 = t ['call']
                print('call:',s1)
                s2 = t ['retv']
                print('retv:',s2)
                s3 = t ['desc']
                print('desc:',s3)
                c += 1
        print("count:",c)
        #print(('\n'*5))

    elif s==5:
        antwort = hkr_obj.get_heizkreis_config(0,1)
        print()
        print("="*70)
        print("test: Einlesen der Konfigurationsdaten 0: des aktiven Heizkreises")
        print("-"*70)
        print(str(antwort))
        antwort = hkr_obj.get_heizkreis_config(1)
        print()
        print("="*70)
        print("test: Einlesen der Konfigurationsdaten 1: des aktiven Heizkreises")
        print("-"*70)
        print(str(antwort))

        print()
        e = terc_obj.gtb()
        print(e[2]['calib_valve'])

    pass
