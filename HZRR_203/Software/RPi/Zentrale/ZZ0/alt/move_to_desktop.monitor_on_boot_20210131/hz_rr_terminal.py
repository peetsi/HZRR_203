import time
from itertools import zip_longest

import PySimpleGUI as sg

import hz_rr_config as cg
import hz_rr_debug as dbeg
import hz_rr_terminal_defines as td
import usb_ser_b as us
from hr2_variables import *
from usb_ser_b import ser_add_work

    #import PySimpleGUIQt as sg
#finally:
#    print("[hz_rr_terminal.py] - module import error")

dbg  = dbeg.Debug(1)

class hz_rr_Terminal(td.hz_rr_Terminal_defines):

    def __init__(self):
        us.ser_obj.terminal_running = False
        self.window                 = ""
        self.dbg                    = dbg
        self.__sel_cmd              = ""
        self.__sel_cmd_o            = ""
        self.command_history        = []
        self.help                   = super().__init__()
        self.terminal_identifier    = "TERMINAL"
        _meh                        = cg.terc_obj.gtb()
        self.cmd_e                  = _meh[2]
        self.cmd                    = _meh[1]                                           #make last used from cache
        self.Send_configure         = [[sg.InputCombo(self.cmd,key='txstr',default_value='',size=(70, 1),background_color='black', text_color='green', font='inconsolata' ) ,sg.RButton('send')]]
        mytext                      = '[TERMINAL WINDOW]\n\n - 1. SELECT COMMAND TO RECEIVE EXPLANATION.\n - 2. AFTER SENDING THE FIRST COMMAND, YOU WILL GET A CONSOLE OUTPUT INSTEAD.'
        self.layout                 = [[sg.Multiline(mytext, key='message', background_color='black', text_color='green', font='inconsolata', size=(90,30))],
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
                        self.dbg.m("value['txstr']: NoneType error", cdb = -7)
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
                self.dbg.m("button:[",button,"]value:[",value,"]",cdb=11)

                try:
                    pass
                finally:

                    if button=='__TIMEOUT__':
                        pass

                    elif button==None and value==None:
                        self.dbg.m('end program2')
                        isRun=False

                    elif button=='txstr':
                        self.dbg.m("test")

                    elif button=='send':
                        #get function call from box
                        #send to universal handler.. write now
                        v=value['txstr'] + "," + self.terminal_identifier
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

                                append_query = ("-"*30) + "[COMMAND USED]\n" + str(t[:-1]) + "\n" + rsp
                                self.command_history.append(append_query)
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
            self.dbg.m("end terminal")

    def __set_selcmd(self,s):
        self.__sel_cmd = s
        try:
            if us.ser_obj.terminal_running == True:
                try:
                    self.window.FindElement('message').Update(self.__sel_cmd)
                except Exception as e:
                    self.dbg.m("self.window.FindElement exception:", e, cdb = -7)
                    pass
        finally:
            self.dbg.m("__set_selcmd: [UNCHANGED]",cdb=11)
        return

    def __empty_box(self):
        try:
            self.window.FindElement('message').Update("")
        except Exception as e:
            self.dbg.m("self.window.FindElement exception:", e, cdb = -7)
            pass

term_obj = hz_rr_Terminal()


if __name__ == "__main__":
    us.ser_obj.ser_check()
    t = hz_rr_Terminal()
    t.runme()
