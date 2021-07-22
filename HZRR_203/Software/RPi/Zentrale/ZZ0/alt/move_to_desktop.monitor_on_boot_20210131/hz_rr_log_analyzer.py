
import PySimpleGUI as sg
import hz_rr_debug as dbg
import copy

class hz_rr_log_analyzer():

    def __init__(self):

        sg.ChangeLookAndFeel('Dark')
        self._header_line           = 'Log Analyzer'
        self.location               = (600,600)
        self.ende                   = False
        self.layout                 = self.__gen_layout('test')
        self.dbg                    = dbg.Debug(1)

    def runme(self):
        self.form                   = sg.FlexForm(self._header_line)#, default_element_size=(800, 400))
        event, value                = self.form.Layout(self.layout).Read()
        while not self.ende:             # Event Loop

            print(event, value)
            #for _w in self._cmd_list:
            if event is None or event == 'Zurück':
                self.ende = True
                self.form.Close()
                return
            elif event == '__TIMEOUT__':
                pass
                #event, values = form.Layout(layout).Read()
            #elif event == _w:
            #    print("send function comes here")
            #    use = ""
            #    try:
            #        #use = self._cmd_and_function_dict[_w]
            #        mod = value['cmod']
            #        #reg = value['creg']
            #        #dir = value['cdir']
            #        #dur = value['cdur']
            #        #use = use.format(mod,reg,dir,dur)
            #    except Exception as e:
            #        self.dbg.m("value['txstr']:",e, cdb = -7)
            #    #    txt = "error"
            #    #_q = ( use ,self.gui_terminal_ident)
            #    #_r = us.ser_add_work(_q, cbt=1)
            #    print("_r:")


            layout = self.__gen_layout(self._cmd_list)
            self.form.Close()
            form = sg.FlexForm(self._header_line, default_element_size=(40, 1))
            event, value = form.Layout(layout).Read()

    def __gen_layout(self, to_gen):
        self.__def_layout()

        self._layout['elements']    = dict()
        for _k in self._layout.keys():
            self._layout['elements'][_k] = dict()
            #self._layout['elements'][_k][] = dict()
        self.__create_layout()

        _filter_time = [[sg.Text('... nach Zeit von:'),sg.Text("bis:"),],
                        [sg.Combo("H",key="_fh"),sg.Combo("M",key="_fm"),sg.Combo("S",key="_fs"),
                         sg.Combo("H",key="_th"),sg.Combo("M",key="_tm"),sg.Combo("S",key="_ts")]]

        _filter_thread= [[sg.Text('... nach Threads:'),],
                        [sg.Combo('Thread',default_value='Thread',)]]

        _filter_fname = [[sg.Text('...nach Dateiname:')]]

        _frame_sel_log  = [[sg.Text('Wähle eine log Datei aus'),],
                            [sg.Input(''),sg.Button('select')]]

        _frame_sel_time = []


        _lay = [[sg.Frame('Wähle Logdatei aus', _frame_choose_log),],
                [sg.Text('Filter..'),],
                [_filter_time,],
                [],
                #[sg.Listbox("output", size=(800, 5), key="logdisplay", default_text='output', background_color="green"),]]
        return _lay


    #def __init__(self, values, default_values=None, select_mode=None, change_submits=False, enable_events=False,
    #             bind_return_key=False, size=(None, None), disabled=False, auto_size_text=None, font=None, no_scrollbar=False,
    #             background_color=None, text_color=None, key=None, k=None, pad=None, tooltip=None, right_click_menu=None,
    #             visible=True, metadata=None):

        #return   [[sg.Text('Wähle eine Log Datei'),],
        #            # [sg.Input(do_not_clear=True, key='_IN_')],
        #            [],
        #            *[[sg.Button(button_text=w,key=w)] for w in _cmd_list],
        #            [sg.Button('Zurück')]]

    def __create_layout(self):
        _l = copy.deepcopy(self._layout)
        print("test:",_l.keys())
        # get and create them all
        _l['elements'] = dict()
        for _gui_elements, _val in _l.items():
            for _gui_element_name in _val.keys():
                self._layout['elements'][_gui_elements] = dict()
                self._layout['elements'][_gui_elements][_gui_element_name] = dict()
                self._layout['elements'][_gui_elements][_gui_element_name]['pos'] = dict()
                self._layout['elements'][_gui_elements][_gui_element_name]['pos']['x'] = 0.0
                self._layout['elements'][_gui_elements][_gui_element_name]['pos']['y'] = 0.0
                self._layout['elements'][_gui_elements][_gui_element_name]['pos']['z'] = 0.0

        print("_l:",str(self._layout).replace('},','}\n\n,').replace("': {'","':\n\t{'"))
        #[sg.Combo(                  self._layout['combo']['logfilename']['values'],
        #            key=            self._layout['combo']['logfilename']['key'],
        #            default_value=  self._layout['combo']['logfilename']['default_value'],
        #            size=           self._layout['combo']['logfilename']['size'])]


        #return   [[sg.Text('Wähle eine Log Datei'),],
        #            # [sg.Input(do_not_clear=True, key='_IN_')],
        #            [sg.Combo(self._module_list,key=self.layout_key_combo_logfilename,default_value=self._module_list[0],size=(20,40)), sg.Combo(self._regler_list,key='creg',default_value=self._regler_list[0],size=(20,40))],
        #            *[[sg.Button(button_text=w,key=w)] for w in _cmd_list],
        #            [sg.Button('Zurück')]]


    def __def_layout(self):
        self._layout = dict()

        self._layout['combo']= dict()
        self._layout['combo']['DEFAULT_NAME'] = dict()
        self._layout['combo']['DEFAULT_NAME']['values']                 =   None
        self._layout['combo']['DEFAULT_NAME']['default_value']          =   None
        self._layout['combo']['DEFAULT_NAME']['size']                   =   (None, None)
        self._layout['combo']['DEFAULT_NAME']['auto_size_text']         =   None
        self._layout['combo']['DEFAULT_NAME']['background_color']       =   None
        self._layout['combo']['DEFAULT_NAME']['text_color']             =   None
        self._layout['combo']['DEFAULT_NAME']['change_submits']         =   False
        self._layout['combo']['DEFAULT_NAME']['enable_events']          =   False
        self._layout['combo']['DEFAULT_NAME']['disabled']               =   False
        self._layout['combo']['DEFAULT_NAME']['key']                    =   None
        self._layout['combo']['DEFAULT_NAME']['k']                      =   None
        self._layout['combo']['DEFAULT_NAME']['pad']                    =   None
        self._layout['combo']['DEFAULT_NAME']['tooltip']                =   None
        self._layout['combo']['DEFAULT_NAME']['readonly']               =   False
        self._layout['combo']['DEFAULT_NAME']['font']                   =   None
        self._layout['combo']['DEFAULT_NAME']['visible']                =   True
        self._layout['combo']['DEFAULT_NAME']['metadata']               =   None

        self._layout['button']= dict()
        self._layout['button']['DEFAULT_NAME'] = dict()
        self._layout['button']['DEFAULT_NAME']['button_text']           = ''
        self._layout['button']['DEFAULT_NAME']['button_type']           = sg.BUTTON_TYPE_READ_FORM
        self._layout['button']['DEFAULT_NAME']['target']                = (None,None)
        self._layout['button']['DEFAULT_NAME']['tooltip']               = None
        self._layout['button']['DEFAULT_NAME']['file_types']            = ("ALL Files", "*.*")
        self._layout['button']['DEFAULT_NAME']['initial_folder']        = None
        self._layout['button']['DEFAULT_NAME']['disabled']              = False
        self._layout['button']['DEFAULT_NAME']['change_submits']        = False
        self._layout['button']['DEFAULT_NAME']['enable_events']         = False
        self._layout['button']['DEFAULT_NAME']['image_filename']        = None
        self._layout['button']['DEFAULT_NAME']['image_data']            = None
        self._layout['button']['DEFAULT_NAME']['image_size']            = (None,None)
        self._layout['button']['DEFAULT_NAME']['image_subsample']       = None
        self._layout['button']['DEFAULT_NAME']['border_width']          = None
        self._layout['button']['DEFAULT_NAME']['size']                  = (None,None)
        self._layout['button']['DEFAULT_NAME']['auto_size_button']      = None
        self._layout['button']['DEFAULT_NAME']['button_color']          = None
        self._layout['button']['DEFAULT_NAME']['disabled_button_color'] = None
        self._layout['button']['DEFAULT_NAME']['highlight_colors']      = None
        self._layout['button']['DEFAULT_NAME']['use_ttk_buttons']       = None
        self._layout['button']['DEFAULT_NAME']['font']                  = None
        self._layout['button']['DEFAULT_NAME']['bind_return_key']       = False
        self._layout['button']['DEFAULT_NAME']['focus']                 = False
        self._layout['button']['DEFAULT_NAME']['pad']                   = None
        self._layout['button']['DEFAULT_NAME']['key']                   = None
        self._layout['button']['DEFAULT_NAME']['k']                     = None
        self._layout['button']['DEFAULT_NAME']['visible']               = True
        self._layout['button']['DEFAULT_NAME']['metadata']              = None

        self._layout['text']= dict()
        self._layout['text']['DEFAULT_NAME'] = dict()
        self._layout['text']['DEFAULT_NAME']['size']                    = (None, None)
        self._layout['text']['DEFAULT_NAME']['auto_size_text']          = None
        self._layout['text']['DEFAULT_NAME']['click_submits']           = False
        self._layout['text']['DEFAULT_NAME']['enable_events']           = False
        self._layout['text']['DEFAULT_NAME']['relief']                  = None
        self._layout['text']['DEFAULT_NAME']['font']                    = None
        self._layout['text']['DEFAULT_NAME']['text_color']              = None
        self._layout['text']['DEFAULT_NAME']['background_color']        = None
        self._layout['text']['DEFAULT_NAME']['border_width']            = None
        self._layout['text']['DEFAULT_NAME']['justification']           = None
        self._layout['text']['DEFAULT_NAME']['pad']                     = None
        self._layout['text']['DEFAULT_NAME']['key']                     = None
        self._layout['text']['DEFAULT_NAME']['k']                       = None
        self._layout['text']['DEFAULT_NAME']['right_click_menu']        = None
        self._layout['text']['DEFAULT_NAME']['grab']                    = None
        self._layout['text']['DEFAULT_NAME']['tooltip']                 = None
        self._layout['text']['DEFAULT_NAME']['visible']                 = True



loga_obj = hz_rr_log_analyzer()


def _rnd_float_range(f=30, t=60,  l=3,  r=0):
    import random
    _ret=[]
    _r = ""
    _f = False
    for _repeat in range(0,r+1):
        _r = str(random.randint(f,t))+"."
        for _length in range(0,l):
            _r += str(random.randint(0,9))
        _ret.append( float(_r) )
    return _ret


if __name__ == "__main__":
    loga_obj = hz_rr_log_analyzer()
    loga_obj.runme()

    #_values     = _rnd_float_range(54,61,3,10000)
    #vle         = _values.pop()
    #vle1        = vle
    #vlZen       = vle
    #filtFakt    = 0.25
    #print( f'[{len(_values)}](vle:{vle}, vle1:{vle1}, vlZen:{vlZen})' )    #long list to simulate a night
#
    #while (len(_values)>0):
    #    vle     = _values.pop()
    #    vle1    = vle      * filtFakt + vle1   *   (1-filtFakt)
    #    vlZen   = vle1    * filtFakt + vlZen  *   (1-filtFakt)
    #    print( f'[{len(_values)}](vle:{vle}, vle1:{vle1.__round__(3)}, vlZen:{vlZen.__round__(3)})' )