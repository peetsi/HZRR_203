#!/usr/bin/python3

import inspect
import configparser
import platform

global conf_obj, hkr_obj

configfile_n = "config/hz_rr_config.ini"
hkr_config   = "config/heizkreis.ini"

class Conf:
    #obj         = ""
    #using_conf  = ""
    #initd       = 0

    def __init__(self,using_conf=""):
        self.using_conf = using_conf
        self.obj        = ""
        self.is_linux   = False
        self.islinux()
        self.initd      = 0
        self.i(self.using_conf)

    def islinux(self):
        if platform.system() == "Linux":
            self.is_linux=True
            return True
        return False

    def i(self,n):
        self.using_conf = n
        try:
            self.obj = configparser.ConfigParser()
        except Exception as e:
            return 1, print("object creation error:",e)
        self.obj.read(self.using_conf)
        self.initd = 1

    def r(self, section, key, default="DEFAULT_ERR"):
        if not self.__isinit__(): return False, print("error - please initialize")
        return self.obj.get(section, key, fallback=default, raw=True)

    def ra(self, default="DEFAULT_ERR"):
        if not self.__isinit__(): return False, print("error - please initialize")
        return self.obj.sections()

    def rs(self, section="", default="DEFAULT_ERR"):
        if not self.__isinit__(): return False, print("error - please initialize")
        return dict(self.obj.items(section))

    def w(self):
        if not self.__isinit__(): return False, print("error - please initialize")
        with open(self.using_conf, 'w') as configfile:
            self.obj.write(configfile)

    def __isinit__(self):
        if self.initd: return True
        return False


conf_obj    = Conf()
hkr_obj     = Conf()

if conf_obj.islinux(): configfile_n = "/media/pi/PYTHONUSB/move_to_desktop.monitor_on_boot/config/hz_rr_config.ini"
if hkr_obj.islinux():  hkr_config   = "/media/pi/PYTHONUSB/move_to_desktop.monitor_on_boot/config/heizkreis.ini"

conf_obj.__init__(configfile_n)
hkr_obj.__init__(hkr_config)


if __name__ == "__main__":
    r = conf_obj.r('system', 'serialPort_WIN')
    print(r)
    r = conf_obj.r('system', 'serialPort_PIthree')
    print(r)
    r = conf_obj.r('system', 'serialPort_PIfour')
    print(r)
    r = hkr_obj.ra()
    print(r)
    hn = conf_obj.r('system','hostPath')
    hn = hn if conf_obj.islinux() else 'NOTDEF'
    r = hkr_obj.rs('ZZ3HR2')
    print(r)
    r = r['modul_tvor']
    print(r)
    r = hkr_obj.r('ZZ3HR2', 'modul_tvor')
    print(r)
    pass