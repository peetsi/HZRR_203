#!/usr/bin/python3

import menue01 as mn
import hz_rr_config as cg
import usb_ser_b as us
import modbus_b as mb
import hz_rr_log_n as lg
import log_mon_handler as lmh
import threading as th
import time as ti

#test


lmh = lmh.logs_and_monitor_handler()

if __name__ == "__main__":
    #us.ser_obj.ser_check()

    #mn.draw_menue()
    while True:

        thread_list = []
        thread1 = th.Thread(target=lmh.ls)
        thread_list.append(thread1)
        thread1.start()
        thread2 = th.Thread(target=lmh.dw)
        thread_list.append(thread2)
        thread2.start()

        while True:
            ti.sleep(0.5)


