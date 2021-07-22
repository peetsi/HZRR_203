import math as ma
import time
import time as ti
from itertools import zip_longest
from threading import Thread

import numpy as np
import PySimpleGUI as sg
#import PySimpleGUIQt as sg
import serial as ser

import heizkreis_config as hkr_cfg
import hr2_variables as hrv
import hz_rr_config as cg
import hz_rr_debug as dbeg
import rr_parse as parse
#from graphics import *
import usb_ser_b as us
from hr2_variables import *
from usb_ser_b import ser_add_work

dbg  = dbeg.Debug(1)
h    = hkr_cfg.get_heizkreis_config()

class hz_rr_Terminal_defines:

    def __init__(self):
        self.__first_distance=10
        self.__hfirst_dist=self.__first_distance/2
        self.__line_length=int(cg.conf_obj.r('Terminal','line_length',65))
        self.__ln="\n"
        self.__call_mask =  "%__CALLER__%"
        self.__usage_mask = "%__USAGE__%"
        self.__usage_expl = "%__EXPLANATION__%"
        self.__new_line_appender = self._r('-',self.__line_length/3) + "|" + self._r(' ',self.__hfirst_dist)
        self.__usage_buf = ""
        self.__expl_buf = ""
        self.mask = self.__ln + \
                    self._r(' ',self.__hfirst_dist)+ '[CALL - HELP]]\n'+ \
                    self._r(' ',self.__first_distance) + "+" + self._r('-',self.__line_length) + self.__ln + \
                    self._r(' ',self.__first_distance) + "|" + self._r(' ',self.__hfirst_dist) + "[" + self.__call_mask + "]" + self.__ln + \
                    self._r(' ',self.__first_distance) + "|" + self._r('-',self.__line_length) + self.__ln + \
                    self._r(' ',self.__first_distance) + "|" + self.__ln + \
                    self._r(' ',self.__first_distance) + "|" + self._r(' ',self.__hfirst_dist) + "[USAGE]" + self.__ln + \
                    self._r(' ',self.__first_distance) + "|" + self.__ln + \
                    self._r(' ',self.__first_distance) + "|" + self._r('-',self.__line_length) + self.__ln + \
                    self.__usage_mask + \
                    self._r(' ',self.__first_distance)+ "|" + self._r('-',self.__line_length) + self.__ln + \
                    self._r(' ',self.__first_distance)+ "|" + self.__ln + \
                    self._r(' ',self.__first_distance)+ "|" + self._r(' ',self.__hfirst_dist) + "[EXPLANATION]" + self.__ln + \
                    self._r(' ',self.__first_distance)+ "|" + self.__ln + \
                    self._r(' ',self.__first_distance)+ "|" + self._r('-',self.__line_length) + self.__ln + \
                    self.__usage_expl  + \
                    self._r(' ',self.__first_distance) + "|" + self._r('-',self.__line_length) + self.__ln + \
                    self._r(' ',self.__first_distance) + "|" + self.__ln + \
                    self._r(' ',self.__first_distance) + "+" + self._r('-',self.__line_length) + self.__ln

    def r(self,caller,usage,explanation):
        if usage.find(self.__ln): # multi line usage
            t = usage.split(self.__ln)
            for x in t:
                self.__usage_buf += self.__new_line_appender + x + self.__ln
            usage = self.__usage_buf
        else:
            usage = self.__new_line_appender + usage + self.__ln

        if explanation.find(self.__ln): # multi line usage
            t = explanation.split(self.__ln)
            for x in t:
                self.__expl_buf += self.__new_line_appender + x + self.__ln
            explanation = self.__expl_buf
        else:
            explanation = self.__new_line_appender + explanation + self.__ln

        r = self.mask.replace(self.__call_mask, caller).replace(self.__usage_mask,usage).replace(self.__usage_expl,explanation)
        self.__init__()
        return r

    def _r(self, v,r):
        buf= ""
        for i in range(int(r)):
            buf += str(v)
        return buf

class hz_rr_Terminal(hz_rr_Terminal_defines):

    def __init__(self):
        us.ser_obj.terminal_running = False
        self.window = ""
        self.dbg = dbg
        self.hzkr_conf = h
        self.__sel_cmd   = ""
        self.__sel_cmd_o = ""
        self.command_history = []
        self.help     = hz_rr_Terminal_defines()

        self.cmd= (  'read_stat,mod,reg','ping,mod','send_tvor,mod,float','set_motor_lifetime_status,mod,reg','set_factory_settings,mod',
                        'valve_move,mod,reg,dur,int','set_normal_operation,mod','set_regulator_active,mod,reg,int','set_fast_mode,mod,int',
                        'get_milisec,mod','cpy_eep2ram,mod','cpy_ram2eep,mod','wd_halt_reset,mod','clr_eep,mod','check_motor,mod,reg',
                        'calib_valve,modAdr,reg','motor_off,modAdr,reg','get_motor_current,mod','lcd_backlight,mod,int','get_jumpers,mod',
                        'change_param,str,reg,name,float','get_param,mod,reg','send_param,mod,reg','show_param,name,args*', 'set_param,name,wert')

        self.cmd_e= {'read_stat'                        : self.help.r('read_stat,module,regler','read_stat,4,1',
        'read_stat\n\ndoes return CN2 and CN4 for hz_rr_log_n, hz_rr_monitordirect_02_b and hz_rr_terminal\ncan be safely called from the terminal.'),
                    'ping'                             : self.help.r('ping,module','ping,4',
                    'ping\n\n pings a module\nmodule must be INT\ntries to ping 3 times\nafterwards returns:False\notherwise:True'),
                    'send_tvor'                        : self.help.r('send_tvor,mod,float','send_tvor,4,70.0',
                    'send_tvor\n\n sends the FLOAT number to the MOD\nif failed to send returns:False\notherwise:True'),
                    'set_motor_lifetime_status'        : self.help.r('set_motor_lifetime_status,mod,reg','set_motor_lifetime_status,4,1',
                    'set_motor_lifetime_status\n\n sends the INT number to the MOD\nif failed to send returns:False\notherwise:True'),
                    'set_factory_settings'             : self.help.r('set_factory_settings,mod','set_factory_settings,4',
                    'set_factory_settings\n\n sends a command to initiate the MOD to load\n its restore values from eeprom\nif failed to send returns:False\notherwise:True'),
                    'valve_move'                       : self.help.r('valve_move,mod,reg,dur,int','valve_move,4,1,20000,int',
                    'valve_move\n\n sends a move order to the MOD\nREG = Regler\nDUR = Runtime in ms\nINT = 1 Open, 0 Close\nif failed to send returns:False\notherwise:True'),
                    'set_normal_operation'             : self.help.r('set_normal_operation,mod','set_normal_operation,4',
                    'set_normal_operation\n\n sends an order to MOD to restore hardcoded values.\nif failed to send returns:False\notherwise:True'),
                    'set_regulator_active'             : self.help.r('set_regulator_active,mod,reg,int','set_regulator_active,4,1,1',
                    'set_regulator_active\n\n Activates or Deactivates a regulator\nMOD = module adr\nREG = regler adr\nINT = 1 Active, 0 = Deactive.\nif failed to send returns:False\notherwise:True'),
                    'set_regulator_active'             : self.help.r('set_regulator_active,mod,reg,int','set_regulator_active,4,1,1',
                    'set_regulator_active\n\n Activates or Deactivates a regulator\nMOD = module adr\nREG = regler adr\nINT = 1 Active, 0 = Deactive.\nif failed to send returns:False\notherwise:True'),
                    'set_fast_mode'                     : self.help.r('set_fast_mode,mod,int','set_fast_4e,4,int',
                    'set_fast_mode\n\n MOD = module adr\nREG = regler adr\nINT = 1 Active, 0 = Deactive.\nif failed to send returns:False\notherwise:True'),
                    'get_milisec'                       : self.help.r('get_milisec,mod','get_milisec,4',
                    'get_milisec\n\n MOD = module adr\nREG = regler adr\nINT = 1 Active, 0 = Deactive.\nif failed to send returns:False\notherwise:True'),
                    'cpy_eep2ram'                       : self.help.r('cpy_eep2ram,mod','cpy_eep2ram,4',
                    'cpy_eep2ram\n\n MOD = module adr\nREG = regler adr\nINT = 1 Active, 0 = Deactive.\nif failed to send returns:False\notherwise:True'),
                    'cpy_ram2eep'                       : self.help.r('cpy_ram2eep,mod','cpy_ram2eep,4',
                    'cpy_ram2eep\n\n MOD = module adr\nREG = regler adr\nINT = 1 Active, 0 = Deactive.\nif failed to send returns:False\notherwise:True'),
                    'wd_halt_reset'                     : self.help.r('wd_halt_reset,mod','wd_halt_reset,4',
                    'wd_halt_reset\n\n MOD = module adr\nREG = regler adr\nINT = 1 Active, 0 = Deactive.\nif failed to send returns:False\notherwise:True'),
                    'clr_eep'                           : self.help.r('clr_eep,mod','clr_eep,4',
                    'clr_eep\n\n MOD = module adr\nREG = regler adr\nINT = 1 Active, 0 = Deactive.\nif failed to send returns:False\notherwise:True'),
                    'check_motor'                       : self.help.r('check_motor,mod,reg','check_motor,4,1',
                    'check_motor\n\n MOD = module adr\nREG = regler adr\nINT = 1 Active, 0 = Deactive.\nif failed to send returns:False\notherwise:True'),
                    'calib_valve'                       : self.help.r('calib_valve,modAdr,reg','calib_valve,4Adr,1',
                    'calib_valve\n\n MOD = module adr\nREG = regler adr\nINT = 1 Active, 0 = Deactive.\nif failed to send returns:False\notherwise:True'),
                    'motor_off'                         : self.help.r('motor_off,modAdr,reg','motor_off,4Adr,1',
                    'motor_off\n\n MOD = module adr\nREG = regler adr\nINT = 1 Active, 0 = Deactive.\nif failed to send returns:False\notherwise:True'),
                    'get_motor_current'                 : self.help.r('get_motor_current,mod','get_motor_current,4',
                    'get_motor_current\n\n MOD = module adr\nREG = regler adr\nINT = 1 Active, 0 = Deactive.\nif failed to send returns:False\notherwise:True'),
                    'lcd_backlight'                     : self.help.r('lcd_backlight,mod,int','lcd_backlight,4,int',
                    'lcd_backlight\n\n MOD = module adr\nREG = regler adr\nINT = 1 Active, 0 = Deactive.\nif failed to send returns:False\notherwise:True'),
                    'get_jumpers'                       : self.help.r('get_jumpers,mod','get_jumpers,4',
                    'get_jumpers\n\n MOD = module adr\nREG = regler adr\nINT = 1 Active, 0 = Deactive.\nif failed to send returns:False\notherwise:True'),
                    'change_param'                      : self.help.r('change_param,str,reg,name,float','change_param,"r",1,"dtOffset",77.0,',
                    'change_param\n\n MOD = module adr\nREG = regler adr\nINT = 1 Active, 0 = Deactive.\nif failed to send returns:False\notherwise:True'),
                    'get_param'                         : self.help.r('get_param,mod,reg','get_param,4,1',
                    'get_param\n\n MOD = module adr\nREG = regler adr\nINT = 1 Active, 0 = Deactive.\nif failed to send returns:False\notherwise:True'),
                    'send_param'                        : self.help.r('send_param,mod,reg','send_param,4,1',
                    'send_param\n\n MOD = module adr\nREG = regler adr\nINT = 1 Active, 0 = Deactive.\nif failed to send returns:False\notherwise:True'),
                    'show_param'                        : self.help.r('show_param,mod,reg','send_param,4,1',
                    'show_param\n\n MOD = module adr\nREG = regler adr\nINT = 1 Active, 0 = Deactive.\nif failed to send returns:False\notherwise:True'),
                    'set_param'                        : self.help.r('set_param,mod,reg','send_param,4,1',
                    'set_param\n\n MOD = module adr\nREG = regler adr\nINT = 1 Active, 0 = Deactive.\nif failed to send returns:False\notherwise:True')}
        self.Send_configure =[[sg.InputCombo(self.cmd,key='txstr',size=(70, 1),background_color='black', text_color='green', font='inconsolata' ) ,sg.RButton('send')]]

        mytext = '[TERMINAL WINDOW]\n\n - 1. SELECT COMMAND TO RECEIVE EXPLANATION.\n - 2. AFTER SENDING THE FIRST COMMAND, YOU WILL GET A CONSOLE OUTPUT INSTEAD.'
        self.layout=[[sg.Multiline(mytext, key='message', background_color='black', text_color='green', font='inconsolata', size=(90,30))],
                            [sg.Frame('send area', self.Send_configure)]]                               #inconsolata


    def runme(self):
        outro=""
        try:
            us.ser_obj.terminal_running = True
            self.window = sg.Window('HZ_RR Console Terminal', self.layout,background_color='black')
            #sg.SetOptions(element_padding=(5,9),font=('Verdana',14),input_elements_background_color='#272727',input_text_color='#ffffff')
            ser=None
            text=''
            isRun=True
            while isRun==True:
                time.sleep(0.01)
                button, value = self.window.Read(timeout=100) #nonblocking read

                try:
                    try:
                        txt = value['txstr']
                    except Exception as e:
                        self.dbg.m("value['txstr']: NoneType error", cdb = 3)
                        txt = "error"
                finally:
                    if (txt != "") and (txt != None) and (txt != outro):
                        if txt.find(',') > 0:
                            try:
                                outro=txt
                                txt = txt.split(",")[0]
                                x = self.cmd_e.get(txt)
                                self.__empty_box()
                                self.__set_selcmd(x)
                            except KeyError as e:
                                self.dbg.m("key_error:",e,cdb=1)


                dbg.m("button:[",button,"]value:[",value,"]",cdb=11)

                try:
                    pass
                finally:

                    if button=='__TIMEOUT__':
                        pass

                    elif button==None and value==None:
                        print('end program2')
                        isRun=False

                    elif button=='txstr':
                        print("test")

                    elif button=='send':
                        #get function call from box
                        #send to universal handler.. write now
                        v=value['txstr'] + ",TERMINAL"
                        if v!="":
                            #dbg.m("value[txstr]:",str(v),cdb=2)
                            t = tuple(map(str, v.replace(' ','').split(',')))
                            #dbg.m("tuple:",t,cdb=2)
                            if  len(t) >= 3:
                                r = ser_add_work( t, cbt=1 )
                                rsp = str(us.ser_obj.get_rx_response())
                                if r[0] == False:
                                    sg.Popup('Error:'+str(r))
                                dbg.m("ser_add_work:",r,cdb=2)

                                append_query = v + ": " + rsp
                                self.command_history.append(append_query)
                                #history_offset = len(self.command_history)-1
                                #self.window.FindElement('txstr').Update('') # manually clear input because keyboard events blocks clear
                                self.window.FindElement('message').Update('\n'.join(self.command_history))
                                self.dbg.m(time.strftime('[TERMINAL_ENTRY_AT_%Y%m%d_%H%M%S]\n').join(self.command_history), cdb=-4)
                                self.command_history = [] # reset to avoid spam..
                                #self.window.FindElement('txstr').Update(v)
                            else:
                                dbg.m("no command has been entered")
                    #self.window.FindElement('txstr').Update(button) #Modify the contents of the send box
        finally:
            us.ser_obj.terminal_running = False
            self.window.close()
            print("end terminal")

    def __set_selcmd(self,s):
        self.__sel_cmd = s
        try:
            if us.ser_obj.terminal_running == True:
                try:
                    self.window.FindElement('message').Update(self.__sel_cmd)
                except Exception as e:
                    self.dbg.m("self.window.FindElement exception:", e, cdb = 3)
                    pass
        finally:
            self.dbg.m("__set_selcmd: [UNCHANGED]",cdb=11)
        return

    def __empty_box(self):
        try:
            self.window.FindElement('message').Update("")
        except Exception as e:
            self.dbg.m("self.window.FindElement exception:", e, cdb = 3)
            pass

term_obj = hz_rr_Terminal()


if __name__ == "__main__":
    us.ser_obj.ser_check()
    t = hz_rr_Terminal()
    t.runme()
