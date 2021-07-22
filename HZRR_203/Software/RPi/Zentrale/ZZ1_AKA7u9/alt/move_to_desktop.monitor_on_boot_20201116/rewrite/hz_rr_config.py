#!/usr/bin/python3

import inspect
import configparser

configfile_n = "hz_rr_config.ini"

class Conf:
    obj         = ""
    using_conf  = ""
    initd       = 0

    def __init__(self,using_conf=""):
        self.using_conf = using_conf
        self.obj = ""
        self.i(self.using_conf)
        
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
        return self.obj.get(section, key, fallback=default,raw=True)

    def w(self):
        if not self.__isinit__(): return False, print("error - please initialize")
        with open(self.using_conf, 'w') as configfile:
            self.obj.write(configfile)

    def __isinit__(self):
        if self.initd: return True
        return False

conf_obj = Conf(configfile_n)

if __name__ == "__main__":
    r = conf_obj.r('system', 'serialPort')
    print(r)
    pass