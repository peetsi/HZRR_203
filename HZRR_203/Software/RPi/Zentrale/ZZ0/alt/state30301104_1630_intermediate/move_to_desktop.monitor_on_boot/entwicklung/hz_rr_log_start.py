#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
hz-rr : start logger - script
ersetzt das frühere shell-script

"""
import subprocess
import time
import threading
import os, sys

PROGPATH = "/home/pi/Desktop/monitor/"
PROGNAME = "hz_rr_log.py"
PROGPATHNAME = PROGPATH+PROGNAME
LOGFILE  = "%s/log/loglog.txt"%(PROGPATH)
tstruct  = time.localtime()
NOW      = time.strftime("%Y-%m-%d %H:%M:%S",tstruct)

def print_usage():
    usage = "Usage: %s {start|startsilent|stat|stop}"%(args[0])
    print(usage)
    sys.exit( 1 )

print(PROGPATH,PROGNAME,LOGFILE,NOW)

rv  = os.chdir(PROGPATH)
rv  = os.getcwd()
print(rv)




args = sys.argv
if len(args) != 2:
    print_usage()
      
cmd = args[1]
if cmd == "start" or cmd == "startsilent":
    # startsilent echos stdout also to log-file
    rv = subprocess.check_output(["ps","-aux"]).decode("utf-8")
    flog = open(PROGPATH+"log/loglog.txt","a")
    if PROGNAME in rv:
        hs = "1 - " + NOW + ": " + PROGNAME + " ist bereits aktiv"
        print(hs)
        flog.write(hs+"\n")
    else:
        hs = "2 - "+ NOW + ": " + PROGNAME + " wird gestartet"
        print(hs)
        os.system(PROGPATHNAME)
        #subprocess.Popen(PROGPATHNAME)
        flog.write(hs+"\n")
    flog.close()

elif cmd == "stop":   
    rv = subprocess.check_output(["ps","-aux"]).decode("utf-8")
    flog = open(PROGPATH+"log/loglog.txt","a")
    if PROGNAME in rv:
        hs = "3 - " + NOW + ": " + PROGNAME + " wird beendet"
        print(hs)
        flog.write(hs+"\n")
        os.system("pkill -f %s"%(PROGNAME))
        #rv = subprocess.check_output(["pkill", "-f", PROGNAME]).decode("utf-8")
        print(rv)
        flog.write(rv+"\n")
    else:
        hs = "4 - " + NOW + ": " + PROGNAME + " lief nicht"
        print(hs)
        flog.write(hs+"\n")
    flog.close()
    
elif cmd == "stat":   
    rv = subprocess.check_output(["ps","-aux"]).decode("utf-8")
    flog = open(PROGPATH+"log/loglog.txt","a")
    if PROGNAME in rv:
        hs = "5 - " + NOW + ": " + PROGNAME + " läuft"
        print(hs)
        flog.write(hs+"\n")
    else:
        hs = "6 - " + NOW + ": " + PROGNAME + " läuft nicht"
        print(hs)
        flog.write(hs+"\n")
    flog.close()
    
'''
elif cmd == "startsilent":   
    rv = subprocess.check_output(["ps","-aux"]).decode("utf-8")
    flog = open(PROGPATH+"log/loglog.txt","a")
    if PROGNAME in rv:
        hs = "7 - " + NOW + ": " + PROGNAME + " ist bereits aktiv"
        print(hs)
        flog.write(hs+"\n")
    else:
        hs = "8 - " + NOW + ": " + PROGNAME + " wird gestartet (ruhig)"
        print(hs)
        flog.write(hs+"\n")
        p=subprocess.Popen(
            PROGPATHNAME,
            stdout = subprocess.PIPE,
        )
        for line in iter(p.stdout.readline, b""):
            flog.write(line.decode("utf-8"))
            flog.flush()
        flog.close()
'''
sys.exit( 0 )
