#!/usr/bin/python3
import menue01 as mn
import hz_rr_config as cg
import usb_ser_b as us
import modbus_b as mb
import hz_rr_log_n as lg
import multiprocessing
from multiprocessing import Process, Pipe
import threading as th
import time as ti
import hz_rr_debug as dbg
from queue import Queue
import time
import platform

dbg = dbg.Debug(1)


class logs_and_monitor_handler():

    #print_lock = th.Lock()

    def __init__(self):
        # ~ set locals - easier to use
        self.thread_output=[""]
        # init serial connection as it is mandatory for procedure.
        us.ser_obj.ser_check()
        # cg.conf_obj
        # mn.menu_obj
        # lg.log_obj
        # us.ser_obj

    def dw(self):
        mn.menu_obj.draw_menue()
    #    ret= ['[MENUE]', 0, 'menu drawn.']
    #    self.thread_output.append(ret)
    #    conn.send(ret)
    #    conn.close()

    def ls(self):
        #ret= ['[LOG]', 0, 'log started.']
        while True:
            lg.log_obj.rr_log()
        #self.thread_output.append(ret)
        #conn.send(ret)
        #conn.close()
    



if __name__ == "__main__":  # important process guard for cross-platform use
    #mn.draw_menue()
    lmh = logs_and_monitor_handler()
#
#    lmh.lg.rr_log()
#    lmh.us.ser_check()
#    lmh.us.get_log_data(4,1,2)
#    lmh.mn.draw_menue()

    pc, cc = Pipe()
    pcc,ccc= Pipe()
    
    thread_list = []
    
    thread1 = th.Thread(target=lmh.ls)
    thread2 = th.Thread(target=lmh.dw)
    
    thread_list.append(thread1)
    thread_list.append(thread2)

    thread1.start()
    thread2.start()

   # q.put(job)


    while True:
        ti.sleep(0.5)

    #thread = threading.Thread(target=lmh.dw, args=(ccc,))
    #thread_list.append(thread)
    #thread.start()
    #x = Process(target=lmh.dw, args=(cc,))
    #y = Process(target=lmh.ls, args=(ccc,))
    #x.start()
    #thread.start()
    #while (x.is_alive() or y.is_alive()):
    #print(pc.recv())
    #print(pcc.recv())
    #x.join()
    #thread.join()


   #def th_block(self):
   #    with self.print_lock:
   #        dbg.m(worker)

   #def threader(self,q):
   #    while True:
   #        # get the job from the front of the queue
   #        self.th_block(q.get())
   #        q.task_done()
   #    

   #q = Queue()
   #for x in range(5):
   #    thread = th.Thread(target = threader)
   #    # this ensures the thread will die when the main thread dies
   #    # can set t.daemon to False if you want it to keep running
   #    th.daemon = True
   #    th.start()

   #for job in range(10):
   #    q.put(job)

