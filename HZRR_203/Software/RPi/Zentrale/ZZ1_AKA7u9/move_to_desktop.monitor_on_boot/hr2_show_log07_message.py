#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
show messages from a running background program
use input texts from a file to be displayed
prompt for end - or stop after a timeout

last modified
Version 
01   pl   initial release
06   pl   adopted for actual plot-program
"""

import time
from tkinter import *

infofileG = None
lblG = None

def change_label():
    global infofile
    global lblG
    lbl = lblG
    try:
        fin = open(infofileG,"r")
    except Exception as e:
        print(e)
    text = fin.read()
    fin.close()
    text.replace("1* ","")
    print(text)
    lbl.config(text=text)
    lbl.update_idletasks()


def win_info_show( headline, infofile ):
    global infofileG
    global lblG
    infofileG = infofile
    win = Tk()
    e=""
    text="***"
    time.sleep(1)
    ende=False
    win.title(headline)
    lbl = Label(win,text=text, width=100,height=10)
    lblG = lbl
    lbl.pack()
    lbl.grid(column=0, row=0)

    win.after( 1000, change_label )
    win.after(30000, lambda : win.destroy())
    win.mainloop()        
    
if __name__ == "__main__":
    win_info_show( "Fortschritt", "message/msgEval.txt" )



