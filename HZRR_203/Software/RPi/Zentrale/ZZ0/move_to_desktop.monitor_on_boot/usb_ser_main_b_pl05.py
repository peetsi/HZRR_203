#!/usr/bin/env python3
# -*- coding: utf-8 -*-


# ----------------
# ----- test -----
# ----------------

if __name__ == "__main__" :

    '''
    =================== NOTE ============================
    There are two files with functions working togehter:
    1. this file "usb_ser_b.py"
        with functions sending commands to a module
    2. "hr2_pars_answer.py"
        with a function to parse the answert from a
        module
    This was useful beause:
        + the files became too big
        + you can easily switch between them
        + common operations for each received data string
          can be performed at once
    =================== NOTE ============================
    '''
import time
import os
import serial

import hr2_parse_answer as pan
import modbus_b as mb
import vorlaut as vor
import usb_ser_b as us
from usb_ser_b import ser_add_work

from hr2_variables import *
import copy
import hz_rr_debug as dbg
#import heizkreis_config as hkr_cfg
import hz_rr_config as cg
hkr_cfg = cg.hkr_obj

dbg = dbg.Debug(1)

def get_modules():
    antwort = hkr_cfg.get_heizkreis_config(0,1)
    return( antwort[1] )

def all_mod_regs(mods):
    lAll=[]
    for mod in mods:
        lAll.append( (mod,0) )
        lAll.append( (mod,1) )
        lAll.append( (mod,2) )
        lAll.append( (mod,3) )
    print(lAll)
    return lAll


def req_get_param(mod,reg,ident) :
    _qu=("get_param",mod,reg,ident)
    return _queue(_qu)

    us.ser_obj.request(("get_param",mod,reg,ident))
    while not us.ser_obj.response_available(ident):   # wait for answer            # in response_available has to be added a TTL value.
        pass

    r = us.ser_obj.get_response(ident)
    if r[0] == False:
        dbg.m("error reading params",cdb=2)

    return r

        
def _queue(d=("get_param",8,3,'ident')):
    _q  = d
    _work, _retv = us.ser_add_work(_q)
    if _work== False: # give back default variables
        dbg.m("_queue _work:",_work," - resetting cn(l)",cdb=1)
    z   = _retv[1]# <<- should be read_stat_str # us.ser_obj.read_stat_str
    dbg.m("_queue z:",z,cdb=3)
    return _work, _retv

def req_set_param(mod,reg,ident): 
    ''' send values in variable "parameter" to module '''
    _qu=("send_param",mod,reg,ident)
    a = _queue(_qu)
    return a

    ''' some  old stuff:
    us.ser_obj.request(("send_param",mod,reg,ident))
    while not us.ser_obj.response_available(ident):   # wait for answer            # in response_available has to be added a TTL value.
        pass

    r = us.ser_obj.get_response(ident)
    if r[0] == False:
        dbg.m("error sending params",cdb=2)

    return r
    '''

def read_parameter( mod, reg ):
    ''' read parameters from modules
        repeat and compare several tries '''
    success_all=True

    success,retval = req_get_param(mod,reg,ident)
    time.sleep(0.1)
    if success: 
        p0=copy.deepcopy(parameter)
    else:
        success_all=False
        p0="p0 empty"
    time.sleep(0.1)

    success,retval = req_get_param(mod,reg,ident)
    if success: 
        p1=copy.deepcopy(parameter)
    else:
        success_all=False
        p1="p1 empty"
    time.sleep(0.1)

    success,retval = req_get_param(mod,reg,ident)
    if success: 
        p2=copy.deepcopy(parameter)
    else:
        success_all=False
        p2="p2 empty"
    time.sleep(0.1)

    diff=""
    if "empty"in p0:
        diff += p0
    if "empty"in p1:
        diff += p1
    if "empty"in p2:
        diff += p2
    if p0!=p1 :
        diff += " p0!=p1"
    if p1!=p2:
        diff += " p1!=p2"
    if p0!=p2:
        diff += " p0!=p2"
    if diff != "":
        success_all = False
    return success_all, diff

    # ******** to test ********************************************

    # ****************************************************
if __name__ == "__main__" :
    ''' history
        27.01.2021  pl  worked over for serial changes in installation
    '''
    
    print("*****************************")
    print("usb_ser_main_b_pl01.py")
    print("check commands to modules")
    print("perform function checks")
    print("*****************************")

    hostname = cg.hkr_obj._get_hostname()
    modules = get_modules()

    parameterPath = "parameter/"
    paramRxFile = parameterPath+"paramRx.dat"
    
    mList = []
    #mList = all_mod_regs(modules)
    #mList = [(1,0),(1,1),(1,2),(1,3),(2,0),(2,1),(2,2),(2,3)]
    #mList = [(1,0),(1,1)]
    fnc = 0      # skip simple test functions
    #fnc = 1      # ping all (module,regulator) pairs in mList
    #TODO: CHECK! fnc = 2      # read status info from pairs in mList
    #fnc = 3      # read parameter info from pairs in mList
    #fnc = 4      # read parameter and save them to file
    #fnc = 5      # read-modify-write parameters ATT: fill in settings in code
    #fnc = 6      # write parameters in Arduino nano to eeprom making it permanent
    fncText=["none","ping","read status","read parameters","read parameter and store in file",
             "read-modify-write parameters","write parameters->eeprom in module",
             "","","","","","","","","","","",]
    # *** check python - version
    import platform
    pyVers = platform.python_version()
    print("Python Version: ",pyVers)
    if pyVers < "3.6":
        print("must be at least Python 3.6")
        sys.exit(1)

    # *** prepare connections
    print("open RS485 network")
    ser = us.ser_obj.ser_check()

    ident = "usb_ser_b_main_pl"  # identity for queue returning data
    # open an output file if necessary
    if fnc == 4 :  # 
        if not os.path.exists(parameterPath):
            os.makedirs(parameterPath)

        fout = open(paramRxFile,"w")
    # *** perform selecte work on all modules from mList
    mListDone = []              # sucessfully performed
    mListOrig = mList.copy()    # original list of regulators to be worked on
    for x in mListOrig:
        mod = x[0]
        reg = x[1]
        print("command to module %d regulator %d"%(mod,reg))

        # *** some simple checks for communication
        #     comment out if not used
        if fnc == 0 :
            pass
        if fnc == 1 :
            # ping a module
            success,repeat=us.ser_obj.ping(mod)
            if success == True:
                mListDone.append( mList.pop(0))
            time.sleep(0.1)

        if fnc == 2 :
            retval=None
            # read status from a module
            us.ser_obj.read_stat(mod,reg)     # result is in cn2 and cn4
            #retval = us.ser_obj.request(("read_stat",mod,reg,ident))
            time.sleep(0.1)
            print("*** fnc=%d, retval="%(fnc),retval)
            print("    cn2=",cn2,"cn4=",cn4)

        if fnc == 3 :
            success,retval = req_get_param(mod,reg,ident)
            if success == True:
                mListDone.append( mList.pop(0))
            time.sleep(0.1)
            print("parameter of mod%d-reg%d : "%(mod,reg),end="")
            if success :
                 print(parameter)
            else:
                print( "ERROR receiving parameter" )

        if fnc == 4 :
            # read parameters from modules and store them to a file
            # repeat and compare several tries
            success,diff = read_parameter(mod,reg)
            if success:
                mListDone.append( mList.pop(0))
            if diff=="":
                fout.write("mod%d,reg%d,"%(mod,reg) + str(parameter) + "\n")
            else:
                fout.write("mod%d,reg%d,"%(mod,reg) + "differences: %s"%(diff) + "\n")

        if fnc == 5 :
            # read parameters from modules, change and write back to module
            #     1. read parameter from module
            success,diff = read_parameter(mod,reg)
            if not success:
                continue

            #     2. change selected values
            #        read values are in variable 'parameter'
            parameter["r"][reg]["pFakt"] = 0.025
            parameter["r"][reg]["iFakt"] = 0.0
            parameter["r"][reg]["dFakt"] = 0.0
            paramNew = copy.deepcopy(parameter)

            #     3. send parameters to module - regulator
            success,st = req_set_param(mod,reg,ident)
            if not success:
                continue
            
            #     4. read back for control
            success,diff = read_parameter(mod,reg)
            if not success:
                continue
            if parameter != paramNew:
                continue
            # getting here: change was successful 
            mListDone.append( mList.pop(0))



        if fnc == 6:
            # write parameters in Arduino nano to eeprom making it permanent
            pass

    time.sleep(0.1)
    print("close network")
    us.ser_obj.ser.close()



    if fnc == 4 :  # 
        fout.close()

    # final status message
    print("Operation %d '%s' ready:"%(fnc,fncText[fnc]))
    print("successfully operated (mod,reg):",mListDone)
    print("no success at         (mod,reg):",mList)

    sys.exit(0)



# ======================================================
# ======================================================
# ======================================================
# FROM  HERE OLD COMMANDS - PROGRAM FUNCTIONS NEW ABOVE
# ======================================================
# ======================================================
# ======================================================

    # *** stress-test commands
    '''
    print(20*"-")
    # generate a rx-buffer overflow in module
    txCmd="123456789 "*25+"\r\n"
    st.rxCmd = txrx_command( txCmd )     # with module address header
    #ser.write(txCmd.encode())             # without addressing
    print(" written",end="")
    ser.flush()
    print(" flushed",end="")
    time.sleep(2)
    print(" wait ready ",end="")
    '''

    #us.get_log_data(4,1,0)
    h = hkr_cfg.get_heizkreis_config()
    if len(h) > 5:
        (heizkreis, modules, modTVor, modSendTvor, dtLog, filtFakt) = h
    else:
        heizkreis   = 0
        modules     = []
        modTVor     = 0
        modSendTvor = []
        dtLog       = 180    # time interval to log a data set
        filtFakt    = 0.1

    mod=1
    
    '''
    # *** Aendere MODUL Parameter
    # *** setzt unteren Wert der Rücklauftemperatur höher:
    #     in den Modul Parametern (sub-Adresse 0)
    us.set_factory_settings(mod)
    us.get_param(mod,0)
    print(parameters[mod]["tr0"],end="->")
    
    parameters[mod]["tr0"]=44
    us.send_param(mod,0)
    print(parameters[mod]["tr0"],end="->")
    us.get_param(mod,0)
    print(parameters[mod]["tr0"])
    '''    
    # *** read commands
    
    # *** modules / regulators to be changed
    modules = []
    # changes for test - mid Jan.2021 - not made permanent - pFakt=0.02, i/d=0 -> success
    # [ (1,1), (2,1), (3,1), (3,3), (4,1), (5,1), (6,1), (6,3), (7,1), (7,3),
    #   (8,1), (8,3), (9,1),(10,1),(11,3),(13,1),(14,1),(15,1),(16,3),(17,1),(17,3)
    # ]
    # changed:
    #parameter["r"][reg]["pFakt"] = 0.02
    #parameter["r"][reg]["iFakt"] = 0.0
    #parameter["r"][reg]["dFakt"] = 0.0

    # changes 27.01.2021:
    toChange=[ (3,3),   (5,3),  (6,3), (7,3),  (9,3), (11,1), (11,3), (13,3),
               (14,3), (15,3), (16,3), (17,3), (18,3), ]   
    # changed:
    #
    # following function fnc selects: 
    #       1:copy parameters from ram to eeprom; 
    #       2:change parameters; 
    #       3:set_factory_settings
    #       4:copy parameters to file
    fnc = 2
    for mod in modules:
        #for reg in [0,1,2,3]:

        if fnc == 3:
            dbg.m("reset old values",cdb=2)
            ser_add_work( ('set_factory_settings,'+str(mod)) )
            dbg.m(mod,"set on factory settings",cdb=2)

        if fnc == 1:
            dbg.m("cpy_ram2eep,",mod,cdb=2)
            ser_add_work( ('cpy_ram2eep',mod) )

        for reg in [2] : 
            '''
            #print("1    - ping(%d) = %s"% (mod, ping(mod)))
            #time.sleep(3)
            #print("2+4  - read_stat(module) =", read_stat(mod,reg))
            # *** get parameters test
            #print("*** 567-0 - get_param(mod,0) =", get_param(mod, 0))
            #p = parameters[mod-1].copy()
            #p.pop("r","r not available")
            #print("len=",len(parameters[mod-1]),len(p))
            #print( p )
            #print("*** 567-1 - get_param(mod,1) =", get_param(mod, reg))
            #print( parameters[mod-1]['r'][reg] )
            #print("*** 567-1 - get_param(mod,1) =", get_param(mod, 1))

            '''

            ident = "return_queue_ser_main_b"
            #reg = 0 
            # *** Aendere REGLER Parameter
            #     1. lies Parameter von den Reglern ein

            i = 0
            if i == 0:
                dbg.m("[req_get_param] 1. lies Parameter von den Reglern ein",cdb=2)
                retval = req_get_param(mod,reg,ident)
                dbg.m("req_get_param:",retval,cdb=2)
                dbg.m("Mod:%d Reg:%d"%(mod,reg),cdb=2)
                #print(parameter["r"][reg-1])
                
                #dbg.m("paramOld:",paramOld,cdb=2)

                #     2. Aendere gewuenschte Parameter
                dbg.m("[parameter] 2. Aendere gewuenschte Parameter",cdb=2)
                dbg.m("pFakt vom Modul=%.3f"%(float(parameter["r"][reg]["pFakt"])))
                #    parameter = parameters[mod]
                #parameter[MOD]["r"][reg]["pFakt"] = 0.03

                parameter["r"][reg]["pFakt"] = 0.02
                parameter["r"][reg]["iFakt"] = 0.0
                parameter["r"][reg]["dFakt"] = 0.0
                paramOld = copy.deepcopy(parameter)
                #parameter["r"][reg]["dtOffset"] = 15000
                #parameter["tr0"] = 44.0
                #dbg.m("parameters[%s]:"%(str(mod)),parameter,cdb=2)
                #dbg.m("neu=%.3f"%(float(parameters[mod]["r"][reg]["pFakt"])))

                #x = (r, 1, dtOffset, 15000)
                #parameter[str] = value  # immer int, wenn erster parameter eine "r" istparameter[str][int]
                #parameter[str][int][str]
                #parameter[str][int][str][int/float]

                #     3. Sende Parameter an Moul-Regler
                dbg.m("[req_set_param] 3. Sende Parameter an Moul-Regler",cdb=2)
                retval = req_set_param(mod,reg,ident)
                #dbg.m("req_set_param:",retval,cdb=2)
                #dbg.m("neu=%.3f"%(float(parameter["r"][reg]["pFakt"])))
                #paramNeu = copy.deepcopy(parameter)
                #dbg.m("paramNeu:",paramNeu,cdb=2)

                #     4. lies Wert zur Überprüfung zurück
                dbg.m("[req_get_param] 4. lies Wert zur Überprüfung zurück",cdb=2)
                retval = req_get_param(mod,reg,ident)
                param_get_new = copy.deepcopy(parameter)
                dbg.m("req_get_param:",retval,cdb=2)
                dbg.m("Mod:%d Reg:%d"%(mod,reg))
                if param_get_new != paramOld :
                    dbg.m("[NEUE PARAMETER WURDEN ÜBERNOMMEN]",cdb=2)
                    dbg.m("param_get_new:",param_get_new,cdb=2)
                    dbg.m("paramOld:",paramOld,cdb=2)
                else:
                    dbg.m("[NEUE PARAMETER WURDEN NICHT ÜBERNOMMEN]",cdb=2)
                    dbg.m("param_get_new:",param_get_new,cdb=2)
                    dbg.m("paramOld:",paramOld,cdb=2)
                #dbg.m("parameters[mod]:",parameter,cdb=2)
                #    dbg.m("Alte und Neue Parameter sind unterschiedlich")
                #if param_get_new == paramNeu :
                #    dbg.m("Neue Parameter wurden übernommen")
            print()


            '''


            # *** set commands
            #print("0x20 - send_Tvor(module) =",    send_Tvor(mod, 44.4)
            #print("0x22 - send_param(module,0) =", send_param(mod,0)
            #print("0x25 - set_motor_lifetime_status(module,reg)=",set_motor_lifetime_status(mod,reg)
            #print("0x30 - factory settings =",     set_factory_settings(mod)
            #print("0x31 - close valve =",          us.valve_move(mod, reg,3000, 0)
            #print("0x34 - set normal operation =", set_normal_operation(mod)
            #print("0x35 - set reg. inactive =",    set_regulator_active(mod,3,0)
            #print("0x36 - fastmode =",             set_fast_mode(mod,1)
            #print("0x37 - get_millisec =",         get_milisec(mod)
            #print("0x38 - cpy_eep2ram=",           cpy_eep2ram(mod)
            #print("0x39 - cpy_ram2eep=",           cpy_ram2eep(mod)
            #print("0x3A - wd_halt_reset=",         wd_halt_reset(mod)
            #print("0x3B - clr_eep=",               clr_eep(mod)
            #print("0x3C - check_motor=",           check_motor(mod,reg)
            #print("0x3D - calib_valve=",           calib_valve(modAdr,reg)
            #print("0x3E - motor_off=",             motor_off(modAdr,reg)
            #print("0x3F - get_motor_current=",     get_motor_current(mod)
            #print("0x40 - lcd_backlight=",         lcd_backlight(mod,0)
            #print("0x41 - jumper setting=",        get_jumpers(mod)
    
    
            print("0x31 -  open valve =",           us.valve_move(mod, reg,20000, 1)
            #print("0x31 - startp. valve =",        us.valve_move(mod, reg, 3000, 2)
            #print("0x31 - startp. valve =",        us.valve_move(mod, 1, 6000, 2)
            #print("0x31 - startp. valve =",        us.valve_move(mod, 1, 3000, 2)
            #print("0x31 - startp. valve =",        us.valve_move(mod, 2, 3000, 2)
            #print("0x31 - startp. valve =",        us.valve_move(mod, 3, 3000, 2)

    '''

    print("close network")
    us.ser_obj.ser.close()
    

