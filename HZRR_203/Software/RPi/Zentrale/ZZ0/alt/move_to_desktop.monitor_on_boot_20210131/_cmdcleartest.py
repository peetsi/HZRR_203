#you will need the win32 libraries for this snippet of code to work, Links below
import win32gui
import win32con
import win32api
import os
from time import sleep
import subprocess, platform

_r = "{"
skp = 2
for i in range(1,31):
    _r += "'"+  str(i) + "':'"
    for x in range(1,4):
        if x != skp: _r += str(x) + ","
    _r = _r[:-1] + "',"
_r += _r[:-1] + "}"
print (_r)

print(_r)
exit(0)
print("e")

sleep(2)
if platform.system()=="Windows":
    subprocess.Popen("cls", shell=True).communicate() #I like to use this instead of subprocess.call since for multi-word commands you can just type it out, granted this is just cls and subprocess.call should work fine 

#[hwnd] No matter what people tell you, this is the handle meaning unique ID, 
#["Notepad"] This is the application main/parent name, an easy way to check for examples is in Task Manager
#["test - Notepad"] This is the application sub/child name, an easy way to check for examples is in Task Manager clicking dropdown arrow
#hwndMain = win32gui.FindWindow("Notepad", "test - Notepad") this returns the main/parent Unique ID
hwndMain = win32gui.FindWindow("Visual Studio Code", "")
print(hwndMain)
hwndChild = os.getpid()
print(hwndChild)
