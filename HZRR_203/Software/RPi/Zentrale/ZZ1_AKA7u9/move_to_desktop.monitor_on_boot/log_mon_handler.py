#!/usr/bin/python3

import copy
import multiprocessing
import platform
import threading as th
import time
import time as ti
from multiprocessing import Pipe, Process

import hr2_variables as hrv
import hz_rr_config as cg
import hz_rr_debug as debg
import hz_rr_log_n as lg
import menue01 as mn
import modbus_b as mb
import usb_ser_b as us
from hr2_variables import *


class logs_and_monitor_handler():

    def __init__(self):
        dbg = debg.Debug(1)
        self.thread_output=[""]
        us.ser_obj.ser_check()

    def dw(self):
        while True:
            mn.menu_obj.draw_menue()
            while us.ser_obj.menu_run == 1:
                pass
            mn.menu_obj.__init__()

    def dummy(self):
        pass

    def ls(self):
        while True:
            x = th.Thread(target=lg.log_obj.rr_log)#, args=(,))  #, args=(q_cmd_log,))
            x.setDaemon(True)
            x.start()
            while x.is_alive():# and us.ser_obj.mon_run == 0:
                time.sleep(1)

    def __del__(self):
        self.dbg.ru()


if __name__ == "__main__":  # important process guard for cross-platform use
    lmh = logs_and_monitor_handler()
    thread_list = []

    worker_log=""
    worker_menu=""
    worker_monitor=""

    while True:
        time.sleep(0.01)

        if worker_log == "":
            worker_log = th.Thread(target=lmh.ls)
            worker_log.setDaemon(True)
            worker_log.start()
            thread_list.append(worker_menu)

        if worker_menu == "":
            worker_menu = th.Thread(target=lmh.dw)
            worker_menu.setDaemon(True)
            worker_menu.start()
            thread_list.append(worker_log)


