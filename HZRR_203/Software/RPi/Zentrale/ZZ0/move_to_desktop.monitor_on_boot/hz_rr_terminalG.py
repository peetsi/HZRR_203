
import PySimpleGUI as sg
import hz_rr_config as cg
import hz_rr_debug as dbg
import usb_ser_b as us
import copy



class hz_rr_terminalG():

    def __init__(self):

        sg.ChangeLookAndFeel('Dark')
        self.heizkreis= self.modules= self.modTVor= \
            self.modSendTvor= self.dtLog= self.filtFakt = None
        self._header_line           = 'Terminal mit Grafischer Oberfläche'
        self.location               = (600,600)
        self.ende                   = False
        self.hkr                    = self.__load_hkr()
        self._cmdlistread           = cg.terg_obj.rs('_cmd_list')
        self._cmd_list              = [x for x in self._cmdlistread.keys()]
        self._module_list           = [x for x in self.modules]
        self._regler_list           = [1,2,3]
        self._cmd_and_function_dict = copy.deepcopy(self._cmdlistread)
        self.layout                 = self.__gen_layout(self._cmd_list)
        self.gui_terminal_ident     = 'hz_rr_terminalG_request'
        self.dbg                    = dbg.Debug(1)

    def runme(self):
        self.form                   = sg.FlexForm(self._header_line, default_element_size=(40, 1))
        event, value               = self.form.Layout(self.layout).Read()
        while not self.ende:             # Event Loop

            print(event, value)
            for _w in self._cmd_list:
                if event is None or event == 'Zurück':
                    self.ende = True
                    self.form.Close()
                    return
                elif event == '__TIMEOUT__':
                    pass
                    #event, values = form.Layout(layout).Read()
                elif event == _w:
                    print("send function comes here")
                    use = ""
                    try:
                        use = self._cmd_and_function_dict[_w]
                        mod = value['cmod']
                        reg = value['creg']
                        dir = value['cdir']
                        dur = value['cdur']
                        use = use.format(mod,reg,dir,dur)
                    except Exception as e:
                        self.dbg.m("value['txstr']:",e, cdb = -7)
                        txt = "error"
                    _q = ( use ,self.gui_terminal_ident)
                    _r = us.ser_add_work(_q, cbt=1)
                    print("_r:",_r)


            layout = self.__gen_layout(self._cmd_list)
            self.form.Close()
            form = sg.FlexForm(self._header_line, default_element_size=(40, 1))
            event, value = form.Layout(layout).Read()

    def __gen_layout(self,_cmd_list):
        return   [[sg.Text('Wähle ein Modul und einen Regler aus und drücke auf den gewünschten Knöpf.\n bei manchen kann eine extra Abfrage für zusätzliche Werte erscheinen.'),],
                    # [sg.Input(do_not_clear=True, key='_IN_')],
                    [sg.Combo(self._module_list,key='cmod',default_value=self._module_list[0],size=(20,40)), sg.Combo(self._regler_list,key='creg',default_value=self._regler_list[0],size=(20,40))],
                    *[[sg.Button(button_text=w,key=w)] for w in _cmd_list],
                    [sg.Button('Zurück')]]
    def __load_hkr(self):
        h = cg.hkr_obj.get_heizkreis_config(0)
        if len(h) > 5:
            #    (heizkreis, modules, modTVor, modSendTvor, dtLog, filtFakt) = h
            (self.heizkreis, self.modules, self.modTVor,
            self.modSendTvor, self.dtLog, self.filtFakt) = h
        else:
            #   # some default values
            #   heizkreis   = 0q
            #   modules     = []
            #   modTVor     = 0
            #   modSendTvor = []
            #   dtLog       = 180    # time interval to log a data set
            #   filtFakt    = 0.1
            self.heizkreis      = 0
            self.modules        = 0
            self.modTVor        = 0
            self.modSendTvor    = []
            self.dtLog          = 180
            self.filtFakt       = 0.1
def _create_buttons():
    (_name, _cmd, _cmd_e, _cmd_all ) = cg.terc_obj.gtb()
    print("_name:",_name,"_cmd:",_cmd)#,"_cmd_e:",_cmd_e,"_cmd_all:",_cmd_all)




terg_obj = hz_rr_terminalG()






if __name__ == "__main__":
    pass
    terg_obj = hz_rr_terminalG()
    terg_obj.runme()
    _create_buttons()