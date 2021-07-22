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

import serial

import hr2_parse_answer as pan
import modbus_b as mb
import vorlaut as vor
import usb_ser_b as us
from usb_ser_b import ser_add_work

from hr2_variables import *
import copy
import hz_rr_debug as dbg
import heizkreis_config as hkr_cfg

dbg = dbg.Debug(1)


def req_get_param(mod,reg,ident) :
    us.ser_obj.request(("get_param",mod,reg,ident))
    while not us.ser_obj.response_available(ident):   # wait for answer            # in response_available has to be added a TTL value.
        pass

    r = us.ser_obj.get_response(ident)
    if r[0] == False:
        dbg.m("error reading params",cdb=2)

    return r

def req_set_param(mod,reg,ident):
    us.ser_obj.request(("send_param",mod,reg,ident))
    while not us.ser_obj.response_available(ident):   # wait for answer            # in response_available has to be added a TTL value.
        pass

    r = us.ser_obj.get_response(ident)
    if r[0] == False:
        dbg.m("error sending params",cdb=2)

    return r

    # ******** to test ********************************************

    # ****************************************************
if __name__ == "__main__" :
    print("*****************************")
    print("usb_ser_b_main.py")
    print("check commands to modules")
    print("*****************************")


    # *** check python - version
    import platform
    pyVers = platform.python_version()
    print("Python Version: ",pyVers)
    if pyVers < "3.6":
        print("must be at least Python 3.6")
        sys.exit(1)




    print("open network")
    ser = us.ser_obj.ser_check()

    #us.read_stat(4,1)     # result is in cn2 and cn4
    #sys.exit(0)

    print(20*"-")
    # *** stress-test commands
    # generate a rx-buffer overflow in module
    '''
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
    #modules=[1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,30]
    #modules=[4]
    for mod in modules:
        #for reg in [0,1,2,3]:

        i = 3
        if i == 3:
            dbg.m("reset old values",cdb=2)
            ser_add_work( ('set_factory_settings,'+str(mod)) )
            dbg.m(mod,"set on factory settings",cdb=2)

        if i == 1:
            dbg.m("cpy_ram2eep,",mod,cdb=2)
            ser_add_work( ('cpy_ram2eep',mod) )

        for reg in range(3) : #[1,3]:
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
            regnr = reg + 1
            # *** Aendere REGLER Parameter
            #     1. lies Parameter von den Reglern ein

            i = 0
            if i == 0:
                dbg.m("[req_get_param] 1. lies Parameter von den Reglern ein",cdb=2)
                retval = req_get_param(mod,regnr,ident)
                dbg.m("req_get_param:",retval,cdb=2)
                dbg.m("Mod:%d Reg:%d"%(mod,regnr),cdb=2)
                #print(parameter["r"][reg-1])
                paramOld = copy.deepcopy(parameter)
                #dbg.m("paramOld:",paramOld,cdb=2)

                #     2. Aendere gewuenschte Parameter
                dbg.m("[parameter] 2. Aendere gewuenschte Parameter",cdb=2)
                dbg.m("pFakt vom Modul=%.3f"%(float(parameter["r"][reg]["pFakt"])))
                #    parameter = parameters[mod]
                #parameter[MOD]["r"][reg]["pFakt"] = 0.03

                parameter["r"][reg]["pFakt"] = 0.03
                parameter["r"][reg]["dtOffset"] = 15000
                parameter["tr0"] = 44.0
                #dbg.m("parameters[%s]:"%(str(mod)),parameter,cdb=2)
                #dbg.m("neu=%.3f"%(float(parameters[mod]["r"][reg]["pFakt"])))

                #x = (r, 1, dtOffset, 15000)
                #parameter[str] = value  # immer int, wenn erster parameter eine "r" istparameter[str][int]
                #parameter[str][int][str]
                #parameter[str][int][str][int/float]

                #     3. Sende Parameter an Moul-Regler
                dbg.m("[req_set_param] 3. Sende Parameter an Moul-Regler",cdb=2)
                retval = req_set_param(mod,regnr,ident)
                #dbg.m("req_set_param:",retval,cdb=2)
                #dbg.m("neu=%.3f"%(float(parameter["r"][reg]["pFakt"])))
                #paramNeu = copy.deepcopy(parameter)
                #dbg.m("paramNeu:",paramNeu,cdb=2)

                #     4. lies Wert zur Überprüfung zurück
                dbg.m("[req_get_param] 4. lies Wert zur Überprüfung zurück",cdb=2)
                retval = req_get_param(mod,regnr,ident)
                param_get_new = copy.deepcopy(parameter)
                dbg.m("req_get_param:",retval,cdb=2)
                dbg.m("Mod:%d Reg:%d"%(mod,regnr))
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
#print("0x25set_motor_lifetime_status(module,reg)=",set_motor_lifetime_status(mod,reg)
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
    
