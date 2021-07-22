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
from hr2_variables import *




    
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
    ser = us.ser_check()

    us.read_stat(4,1)     # result is in cn2 and cn4
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

    us.get_log_data(4,1,0)


    # *** read commands
    #modules=[1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,30]
    modules=[4]
    for mod in modules:
        #for reg in [0,1,2,3]:
        for reg in [1]:
            pass
            #print("1    - ping(%d) = %s"% (mod, ping(mod)))
            #time.sleep(3)
            #print("2+4  - read_stat(module) =", read_stat(mod,reg))
            
                    
            # *** get parameters test
            #parameters_zero()        # clear parameter structure
            #print("*** 567-0 - get_param(mod,0) =", get_param(mod, 0))
            #p = parameters[mod-1].copy()
            #p.pop("r","r not available")
            #print("len=",len(parameters[mod-1]),len(p))
            #print( p )
            #print("*** 567-1 - get_param(mod,1) =", get_param(mod, reg))
            #print( parameters[mod-1]['r'][reg] )
            #print("*** 567-1 - get_param(mod,1) =", get_param(mod, 1))
            

            # *** set commands
            #print("0x20 - send_Tvor(module) =", send_Tvor(mod, 44.4))
            #print("0x22 - send_param(module,0) =", send_param(mod,0))
            #print("0x22 - send_param(module,1) =", send_param(mod,1))
            
            #print("0x25 - set_motor_lifetime_status(module,reg) =", \
            #      set_motor_lifetime_status(mod,reg))
            
            #print("0x30 - factory settings =",set_factory_settings(mod))
            
            # close
            #print("0x31 - close valve =",valve_move(mod, reg,3000, 0))
            # open
            #print("0x31 - open valve =",valve_move(mod, reg,1000, 1))
            # start position
            #print("0x31 - startp. valve =",valve_move(mod, reg, 3000, 2))
            #print("0x31 - startp. valve =",valve_move(mod, 1, 6000, 2))
            #print("0x31 - startp. valve =",valve_move(mod, 1, 3000, 2))
            #print("0x31 - startp. valve =",valve_move(mod, 2, 3000, 2))
            #print("0x31 - startp. valve =",valve_move(mod, 3, 3000, 2))
            
            #print("0x34 - set normal operation =",set_normal_operation(mod))


            #print("0x35 - set reg. inactive =",set_regulator_active(mod,3,0))
            #print("0x35 - set reg. inactive =",set_regulator_active(mod,reg,0))
            #time.sleep(1)
            #print("0x35 - set reg. active =",set_regulator_active(mod,reg,1))
            #time.sleep(1)
            
            #print("0x36 - fastmode =",set_fast_mode(mod,1))
            #print("0x36 - fastmode =",set_fast_mode(mod,0))
            #print("0x37 - get_millisec =",get_milisec(mod))

            #print("0x38 - cpy_eep2ram=",cpy_eep2ram(mod))
            #print("0x39 - cpy_ram2eep=",cpy_ram2eep(mod))
            #print("0x3A - wd_halt_reset=",wd_halt_reset(mod))
            #print("0x3B - clr_eep=",clr_eep(mod))
            #print("0x3C - check_motor=",check_motor(mod,reg))
            #print("0x3D - calib_valve=",calib_valve(modAdr,reg))
            #print("0x3E - motor_off=",motor_off(modAdr,reg))
            #print("0x3F - get_motor_current=",get_motor_current(mod))
            #print("0x40 - lcd_backlight=",lcd_backlight(mod,0))
            #time.sleep(1)
            #print("0x40 - lcd_backlight=",lcd_backlight(mod,1))
            #print("0x41 - jumper setting=",get_jumpers(mod))


    print("close network")
    ser.close()
    
