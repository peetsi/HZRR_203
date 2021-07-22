#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
1. zip all actual files and copy them to a transfer directory
   transfer the zipped file
2. zip all except the files of the last <n> days,
   copy the zip-file to a backup directory
   delete the zipped files

Created on 2021.01.15
Peter Loster (pl)
"""
import glob
import os
import time

logFilePath="/media/pi/PYTHONUSB/move_to_desktop.monitor_on_boot/log/"
sendDir = "../to_send/"
old_log_files_dir = "alt/"
files2zip = "nlogHZ*.dat"
keepDays  = 7  # Tage die im log-dir bleiben, elder files are zipped -> backup directory and deleted

# ***extract data from log-file name to generate zip-file names
#      0123456789 123456789 123456789 123456789 
#     "nlogHZ-RR_ZZ1AKA7u9_20201227_004058.dat"
def extract_dattime( fn ):
    l0 = fn.split("_")  # first file-name
    hk=l0[1]
    d=l0[2]
    t=l0[3].split(".")[0]
    print("hk=%s date=%s time=%s"%(hk,d,t))
    return (hk,d,t)
    

def in_time_range( filename, now, days):
    (hk,d,t) = extract_dattime( filename )
    tf = time.mktime(time.strptime(d+t,"%Y%m%d%H%M%S") )
    dt = days * 24.0 * 3600.0 
    tfile=(now-dt)/3600/24
    print("file is %f days old"%((now- tf)/3600/24))
    if tf < now-dt :
        return False
    else:
        return True


# *** list of all log-files
os.chdir(logFilePath)
lfs = glob.glob(files2zip)  # all log-files in the directory
lfs.sort()
for i in [0,-1]:
    print(i, lfs[i])


(hk,fromDate,fromTime) = extract_dattime( lfs[0] )
(hk,endDate,endTime)   = extract_dattime( lfs[-1])
    

le0 = lfs[-1].split("_")  # last file-name
endDate=le0[2]
endTime=le0[3].split(".")[0]
print("hk=%s endDate=%s endTime=%s"%(hk,endDate,endTime))


# *** zip and copy all files to send-directory
# send file name
zipTxName="hr2Tx_%s_%s-%s_%s-%s.zip"%(hk,fromDate,fromTime,endDate,endTime)
print(zipTxName)
cmd = "zip "+zipTxName
for fn in lfs:
    cmd = cmd+" "+fn
print(cmd)
os.system(cmd)
# TODO - send file to remote host

# copy the zipped file to a send-directory
if not os.path.exists(sendDir):
    os.makedirs(sendDir)
cmd="cp "+zipTxName+" "+sendDir
print(cmd)
os.system(cmd)


# *** select and zip older files, copy to backup dir and delete zipped log-files 
# select files to be zipped for backup and delete
now = time.time()
lBackup=[]
for fn in lfs:
    if not in_time_range(fn,now,keepDays):  # keep files younger than <keepDays> days ago
        lBackup.append(fn)
print("Files to backup and delete: %d from %d"%( len(lBackup), len(lfs)))
print("Files to be deleted:", lBackup)

# make sure bakcup log-file directory exists
if not os.path.exists(old_log_files_dir):
    os.makedirs(old_log_files_dir)
# Backup file name
(hk,endDate,endTime)   = extract_dattime( lBackup[-1])
zipBuName=old_log_files_dir+"hr2Bu_%s_%s-%s_%s-%s.zip"%(hk,fromDate,fromTime,endDate,endTime)
print(zipBuName)
sBackup=""  # string with backup files
for fn in lBackup:
    sBackup = sBackup + " " + fn
    
# zip Backupfiles
cmd = "zip "+zipBuName+" "+sBackup
print(cmd)
os.system(cmd)

# delete zipped backup files from log-directory
cmd = "rm "+sBackup
print(cmd)
os.system(cmd)


# TODO - send file to remote host
pass

