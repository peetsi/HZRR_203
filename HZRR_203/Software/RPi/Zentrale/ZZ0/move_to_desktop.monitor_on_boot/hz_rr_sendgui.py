

import numpy as np
#from graphics import *
import usb_ser_b as us
import heizkreis_config as hkr_cfg
import rr_parse as parse

from hr2_variables import *
import hr2_variables as hrv

import hz_rr_config as cg
import time as ti
import hz_rr_debug as dbeg
import threading as th
#import hz_rr_log_n as lg
import math as ma

dbg  = dbeg.Debug(1)
h    = hkr_cfg.get_heizkreis_config()




class InteractionGUI():

    def __init__(self,m=0):
        self.mode = m

    def test_draw(self):
        if self.mode == 0:
            from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QVBoxLayout
            self.app    = QApplication([])
            self.window = QWidget()
            self.layout = QVBoxLayout()
            self.layout.addWidget(QPushButton('Top'))
            self.layout.addWidget(QPushButton('test'))
            self.layout.addWidget(QPushButton('Bottom'))
            """
                    QLabel
                    QComboBox
                    QCheckBox
                    QRadioButton
                    QPushButton
                    QTableWidget
                    QLineEdit
                    QSlider
                    QProgressBar
            """
            self.window.setLayout(self.layout)
            self.window.show()
            self.app.exec_()
            self.window.close()

        elif self.mode == 1:
            import PySimpleGUI as sg

            sg.theme('DarkAmber')    # Keep things interesting for your users

            rad_module = list()
            for rb in range(1,30):
                rad_module.append(rb)

            radio_list =[1,11,21]+\
                        [2,12,22]+\
                        [3,13,23]+\
                        [4,14,24]+\
                        [5,15,25]+\
                        [6,16,26]+\
                        [7,17,27]+\
                        [8,18,28]+\
                        [9,19,29]+\
                        [10,20,30]

            layout=[[sg.Text('Persistent window')]]
            cnt =1
            teiler=3
            res = []
            buf =[]
            for m in rad_module:
                print("adding:",m,end="")
                buf.append( sg.Radio(m, m, enable_events=True) )
                if cnt%teiler==0:
                    print(".",end="")
                    res.append(buf)
                    del buf
                    buf=[]
                #print("(",cnt%teiler,")",end = "")
                cnt += 1
            print("")

            print(layout)
            layout.append(res)
            print(layout)

#                    [[sg.Radio(m, m, enable_events=True),] for m in rad_module] + \
#*[[[sg.Radio(m, m, enable_events=True),] for m in radio_list]+\
            layout.append( [[sg.Input(key='-IN-')]+\
                            [sg.Button('Read')]+\
                            [sg.Exit()]])
            window = sg.Window('Window that stays open', layout)

            while True:                             # The Event Loop
                event, values = window.read()
                print(event, values)
                if event == sg.WIN_CLOSED or event == 'Exit':
                    break

        """
            Radio(text,
            group_id,
            default=False,
            disabled=False,
            size=(None, None),
            auto_size_text=None,
            background_color=None,
            text_color=None,
            font=None,
            key=None,
            k=None,
            pad=None,
            tooltip=None,
            change_submits=False,
            enable_events=False,
            visible=True,
            metadata=None)
        """
igui_obj = InteractionGUI(1)



if __name__ == "__main__":
    igui_obj.test_draw()
    pass