# last_log.py
#
# first find the newest two files in the log/ directory
#
# then find last record in the newest
# "log/logHZ-RR_YYYYMMDD_hhmmss.dat" file

import os
import glob
import time

pfad = "log/"
suchname=pfad+"logHZ-RR_*"
flist = glob.glob(suchname)
print("Suche nach",suchname)
flist.sort()
for filename in flist:
  print( filename )
lastFile = flist[len(flist)-1]
tsOld    = os.stat(lastFile).st_mtime     # old timestamp

def file_change( file ) :
    global tsOld
    newData = 0
    tsNew = os.stat(file).st_mtime
    print(tsOld,tsNew)
    if tsNew != tsOld:
        newData = 1
        tsOld = tsNew
    else:
        newData = 0
    return newData
    

while not file_change( lastFile ):
  print(".",)
  time.sleep(10)
  pass

time.sleep(20)     # wait for transmission complete

print("open last file: %s"%(lastFile))

datei = open( lastFile,"r")

allLines = 72     # for 1st network
fertig = False
while not fertig:
    # find last set of data for all module addresses
    for line in datei:
        l0=line.strip()
        l1=l0.split()
        tstamp = l1[0]
    tsecLast = time.mktime(time.strptime(tstamp,"%Y%m%d_%H%M%S"))  # time in seconds   
    datei.seek(0)  # rewind from start
    i=0
    for line in datei:
        l0=line.strip()
        l1=l0.split()
        tsecLine = time.mktime(time.strptime(l1[0],"%Y%m%d_%H%M%S"))  # time in seconds 
        if tsecLast - tsecLine < 60.0 :               # the last 50 seconds
          print(i,tstamp,l1[0], tsecLast - tsecLine)
          i += 1
    if i == 72:
        ende = True
        break
    else :
        time.sleep(10)     # wait seconds to complete transmission

print("Fertig")
