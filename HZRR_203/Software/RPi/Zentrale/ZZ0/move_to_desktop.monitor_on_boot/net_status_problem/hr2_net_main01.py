'''
hr2_net_main.py

main program to perform functions for
- RS485 network check and statistics 
- parameter handling
- perform service routines


NOTE
- all modules are imported as a whole to give one
  big, long program file.
  
'''


import time
import os
import platform
import serial
import ast
import glob
import numpy as np
import matplotlib.pyplot as plt

#import hr2_parse_answer as pan
import modbus_b as mb
#import vorlaut as vor
#import usb_ser_b as us
#from usb_ser_b import ser_add_work

#from hr2_variables import *
import copy
#import hz_rr_debug as dbg
#import heizkreis_config as hkr_cfg

# NOTE makes an error on Ubuntu Linux on Notebook PC
#import hz_rr_config as cg
#hkr_cfg = cg.hkr_obj


#print("platform.dist=", platform.dist)
#print("platform.linux_distribution=", platform.linux_distribution)

exit(0)
from hr2_net_var import *      # global variables
from hr2_net_serial import *   # network communication improved
from hr2_net_status01 import * # network status
'''
'''




# -------------------------------------------------------------------
# -------------------------------------------------------------------
# -------------------------------------------------------------------
# -------------------------------------------------------------------
# -------------------------------------------------------------------
# -------------------------------------------------------------------
# -------------------------------------------------------------------
# -------------------------------------------------------------------

if __name__ == "__main__" :
    sErr,ser = ser_check()
    hostname = cg.hkr_obj._get_hostname()
    modules = get_modules()
    #modules = [2]
    testMotors = all_mod_regs( modules, [1,3] )
    #testMotors = [(2,1),(2,3)]
    tests = 1
    print(60*"=")
    print("hostname =",hostname)
    print("modules  =",modules)
    print("tests    =",tests)
    tempPath = "temp/"
    if not os.path.exists(tempPath):
        os.makedirs(tempPath)
    parsPath = "parameter/"
    if not os.path.exists(parsPath):
        os.makedirs(parsPath)
    ts=time.strftime('%Y%m%d-%H%M%S',time.localtime())
    filename = tempPath+"commTest_%s_%s.dat"%(hostname,ts)
    fParsName = parsPath+"params_%s_%s.dat"%(hostname,ts)
    fo = open(filename,"w")

    # send and receive a command directly
    
    # *** test communication
    while True:
        antw = net_test_menu(fo,modules)
        if antw=="0":
            break
        else:
            result=perform(antw,fo,modules,tests)
            #break  # remove for continuous menu
            if result==None:
                print("---> activate selected menu item !")
                break

    ser.close()
    fo.close()

    fin=open(filename,"r")
    filenameSum = filename.rstrip(".dat")+"_sum.dat"
    fos = open(filenameSum,"w")

    # *** evaluate results
    fos.write("---Sum - overview---\n")
    # *** read all data from file and sort into dictionary
    # form: { "m1r3":[n,tmin,tmax,tsum,nErr,orErr], ... }
    mrd={}  # module-regulator-directory
    for line in fin:
        if line[0] != "[":
            continue
        #print(line)
        l0 = line.strip()
        # form of l1: [[txMod,txReg,t0,t1,rxErr]]
        l1 = ast.literal_eval(l0)
        for d in l1:
            t0=d[2]
            t1=d[3]
            dt = t1-t0
            id = "m%dr%d"%(d[0],d[1])
            if id in mrd:
                #[n,tmin,tmax,tsum,nErr,orErr]
                mrd[id][0] += 1
                if dt < mrd[id][1]:
                    mrd[id][1]=dt
                if dt > mrd[id][2]:
                    mrd[id][2]=dt
                mrd[id][3] += dt
                if d[4] != 0 :
                    mrd[id][4] += 1
                mrd[id][5] |= d[4]
            else:
                # add mod/reg to directory 
                e=0
                if d[4] != 0:
                    e=1
                mrd[id] = [1,dt,dt,dt,e,d[4]]

    for id in mrd:
        hs   = id.split("r")
        mod  = int(hs[0][1:])
        reg  = int(hs[1])
        n    = mrd[id][0]
        min  = mrd[id][1]
        max  = mrd[id][2]
        sum  = mrd[id][3]
        nErr = mrd[id][4]
        orErr= mrd[id][5]
        hs="Mod %02d Reg %d: n=%d min=%5.3fs mitt=%5.3fs max=%5.3fs nErr=%2d orErr=%04X"%\
            (mod,reg,n,min,sum/n,max,nErr,orErr )
        print(hs)
        fos.write(hs+"\n")

    '''
    '''
    fos.close()
    pass



