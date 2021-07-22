#!/usr/bin/python3
# -*- coding: utf-8 -*-


#from guizero import App, Text
from guizero import App, PushButton, Text
import subprocess
import time

# Action you would like to perform
def counter0():
    global s0
    text0.value = int(text0.value) + 1
    text1.value = s0

def counter1():
    global s0
    text1.value = s0       # display a status value - but des not
    time.sleep(1)          # a subprocess is called here
    text1.value = "ready"  # only diplays this after a delay

s0="start something after pressing butt1"

app = App("Hello world", layout="grid")

text0 = Text(app, text="1", align="left", grid=[0,1])
text1 = Text(app, text=s0, align="left",grid=[0,8] )
butt1 = PushButton(app, text="Button", command=counter1, align="left", grid=[0,2])
text0.repeat(10000, counter0)  # Schedule call to counter() every 1000ms

app.display()

