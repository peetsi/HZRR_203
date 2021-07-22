#!/usr/bin/python3
import os
import subprocess
import sys
import threading as th
import time as ti

import pkg_resources

import hz_rr_config as cg
import hz_rr_debug as dbeg
import log_mon_handler as lmh

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

def install_dependencies():
    _df_sa   = "guizero,numpy,pysimplegui,pyqt5,matplotlib,varname"
    sa      = cg.conf_obj.r('APT', 'apt_get_list', _df_sa).replace(' ','').split(',')
    apt_get = tuple(map(str,sa[:]))

    required    = set(sa)
    installed   = {pkg.key for pkg in pkg_resources.working_set}
    install     = cg.conf_obj.r('APT', 'install_dependencies', False)
    missing     = required - installed

    if (missing and install):
        python = sys.executable
        x = subprocess.Popen(['sudo', 'python3', '-m', 'pip', 'install', *missing], stdout=subprocess.DEVNULL)
        print(x)


install_dependencies()

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
