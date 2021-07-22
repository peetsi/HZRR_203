#!/usr/bin/python3


import threading as th
import time as ti

#import usb_ser_b as us
#import modbus_b as mb
import hz_rr_config as cg
import hz_rr_debug as dbeg
#import hz_rr_log_n as lg
import log_mon_handler as lmh
import menue01 as mn
import os
import subprocess

global dbg
dbg     = dbeg.Debug()
lmh     = lmh.logs_and_monitor_handler()

def run_bash(file, dopython=0):
    print("starting:", file)
    if (dopython==1):
        return subprocess.Popen("sudo python3 " + file, shell=True)
    #return subprocess.Popen( "sudo /bin/bash " + file, shell=True)
    return os.system("sudo /bin/bash " + file)

def run_cmd(cmd):
    print("executing:", cmd)
    return os.system(cmd)

df_sa   = "guizero,numpy,pysimplegui,pyqt5,matplotlib"
sa      = cg.conf_obj.r('APT', 'apt_get_list', df_sa)
sa      = sa.replace(' ','').split(',')
apt_get = tuple(map(str,sa[:]))

install = cg.conf_obj.r('APT', 'install_dependencies', False)
if install == 1:
    dbg.m("Installing dependencies....",cdb =1 )
    for x in apt_get:
        r = run_cmd('sudo python3 -m pip install ' + x)
        dbg.m('installing:',x,';return:',r,cdb=1)

thread_list = []
thread0 = thread1 = thread2 = ""

dbg.m("Starting Threads..",cdb = 1)
thread2 = th.Thread(target=lmh.dw)
thread2.setDaemon(True)
thread_list.append(thread2)
thread2.start()

thread1 = th.Thread(target=lmh.ls)
thread1.setDaemon(True)
thread_list.append(thread1)
thread1.start()


ti.sleep(0.5)

while True:
    ti.sleep(0.01)
    if not th.Thread.is_alive(thread1):
        dbg.m("Thread status:", th.Thread.is_alive(thread1), "/", \
                                th.Thread.is_alive(thread2))
        thread_list.remove(thread1)
        dbg.ru()
        thread1 = th.Thread(target=lmh.ls)
        thread1.setDaemon(True)
        thread_list.append(thread1)
        thread1.start()
        ti.sleep(0.5)

    if not th.Thread.is_alive(thread2):
        dbg.m("Thread status:", th.Thread.is_alive(thread1), "/", \
                                th.Thread.is_alive(thread2))
        thread_list.remove(thread2)
        dbg.ru()
        #mn.menu_obj.__init__()
        thread2 = th.Thread(target=lmh.dw)
        thread2.setDaemon(True)
        thread_list.append(thread2)
        thread2.start()
        ti.sleep(0.5)

if __name__ == "__main__":
    pass



def _timeit(func):
    """
    Put @_timeit as a decorator to a function to get the time spent in that function printed out

    :param func: Decorated function
    :return: Execution time for the decorated function
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        end = time.time()
        print('{} executed in {:.4f} seconds'.format( func.__name__, end - start))
        return result

    return wrapper
