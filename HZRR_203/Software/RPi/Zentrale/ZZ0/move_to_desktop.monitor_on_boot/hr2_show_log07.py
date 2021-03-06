#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
Created on 2020.11.16
Version 
4a 
5    graphical output worked over
6    read parameters from configuration file


show draft values from Annette-Kollwitz-Anger installation of HZRR-200

@author: pl
"""

import os
import sys
import glob 
from operator import itemgetter
import numpy as np
import time
import matplotlib.pyplot as plt
import shutil
import configparser
import pathlib
import threading

# was changed -> replaced by local parsing of log-data-sets
# import rr_parse as parse


def get_hostname():
    f=open("/etc/hostname","r")
    name = f.read()
    name = name.strip()
    return name


msgEval = None   # static variable for the following function

def set_eval_message( mode, token=0, msg="" ):
    """ set a message to be displayed via gui or sent to log-file """
    """ shows progression and other messages """
    # mode:   
    # 0      open file
    # 1      write message
    # 8      erase file contents
    # 9      close file
    # msg:
    # string containing message
    global msgEval
    evalMsgFilename = "message/msgEval.txt"
    if mode==0:
        if not os.path.isfile(evalMsgFilename):
            print("message file missing, making new file '%s'"%(evalMsgFilename))
            path = evalMsgFilename[ 0 : evalMsgFilename.rfind("/")+1 ]
            pathlib.Path(path).mkdir(parents=True, exist_ok=True) 
        msgEval=open(evalMsgFilename,"w+")  # allow reading and writing
    elif mode==1:
        msgEval.write("%d* %s "%(token,msg) )
    elif mode==8:
        msgEval.truncate(0)
    elif mode==9:
        msgEval.close()

    if mode !=9:
        msgEval.flush()












def select_log_files(path, selectStr):
    """ in directory 'path' copy all log*.dat files into one file; return this filename. """
    #path1=path.rstrip("/")
    flist = glob.glob(path+selectStr)
    flist.sort()
    fcnt=0
    for file in flist:
        fcnt += 1
        print(fcnt, os.path.basename(file))
    print("Verbinde alle Log-Dateien im Verzeichnis '%s'"%(path))
    if len(flist) == 0 :
        print( "Keine Log-Dateien gefunden / abgebrochen" )
        return None

    # *** concatenate all files of form:
    #     "<path>/logHZ-RR_20201019_000958.dat"
    vonFile = os.path.basename(flist[0]).rsplit(".dat")
    bisFile = os.path.basename(flist[-1]).rsplit(".dat")
    print("Verbinde dateien von '%s' bis '%s'"%(vonFile[0],bisFile[0]))

    # make new filename
    sVon = vonFile[0].lstrip("logHRZ-RR_")
    sBis = bisFile[0].lstrip("logHRZ-RR_")
    hsv=sVon[sVon.find("_"):]
    hsb=sBis[sBis.find("_"):]
    hsb=hsb[hsb.find("_",1)+1:]
    sumFileName = "sum" + hsv + "-" + hsb + ".dat"
    print("speichere das Ergebnis in file: ",sumFileName)
    
    # write to output file
    fout=open(path + sumFileName,"w+")
    rzeile=0
    wzeile=0
    print("add file Nr. ",end="")
    for file in flist:
        i = flist.index(file) + 1
        print(i,end=" ")
        fin=open(file,"r")
        for line in fin:
            rzeile+=1
            if len(line) >100:   # ignore short lines - they are incomplete
                wzeile+=1
                fout.write(line)
        fin.close()
    fout.close()
    print()
    print("%d Zeilen gelesen, %d Zeilen geschrieben"%(rzeile,wzeile))
    return (sumFileName)


def read_all_data( logfileSum ):
    """ read data from logfile lines into a big list; return this list """
    print("read data from %s into a big array"%(logfileSum))

    l10Len     = 4      # number of data items before ':' in data set string
    l20Len     = 18     # number of data items after ':'
    regStatLen = 18     # number of items in dasa-set dirctionary regStat

    try:
        fin = open(logfileSum,"r")
    except Exception as e:
        print(e)
        print("no file to plot")
        return None
    
    # *** statistic data and error detection
    lineCnt=0     # lines read from input
    datCnt =0     # accepted lines from input
    formCnt=0     # datasets with wrong format
    
    zeroCntVM=0   # zero values indicate wrong data read
    zeroCntRM=0
    zeroCntVE=0
    zeroCntRE=0
    zeroCntRS=0
    zeroDsSum=0   # sum of datasets with at least one 0-cnt
    fehlerMod=0   # Anfrage und Antwort Modul Adr stimmen nicht ??berein

    fehlerReg=0   # Anfrage und Antwort Regler stimmen nicht ??berein
    fehlerMR =0   # sum of datasets with at least one mod or reg error
    dsProblem=0   # dataset with at least one of the problems above

    # *** read all datasets to a list of data-dictionaries
    dList= []
    for line in fin:
        lineCnt += 1
        l0 = line.strip()

        # ATTENTION !!!     4.12.2020, pl
        #   parse module was changed somehow - did not work any more
        #   -> use own parse functionality here
        #   removed:   p = list( parse.rr_parse(l0) )
        
        # *** parse a line like:
        # 
        # '20201204_124141 1E03 HK2 :00021E1b 
        #  t2146015.5 W VM 54.7 RM 47.5 VE 70.0 RE 47.3 
        #  RS 45.6 P000 E0007 FX44 M4965 A0'
        # 
        # generate an intermediate dictionary like:
        # 
        # {'TST': 1607426818.0, 'MOD': 30, 'REG': 1, 'CMD': 3, 'HK': 2, 'PR': 52,
        #  'TIC': -1804345.5, 'SW': 87, 'VM': 54.8, 'RM': 46.3, 'VE': 0.0, 'RE': 48.7,
        #  'RS': 45.6, 'P': 0.0, 'E': 7, 'FX': 44.0, 'M': 4965.0, 'A': 0.0}
        #
        # and return a numpy array with data-sets of form:
        # idx:        0   1    2   3  4   5           6   7
        # [1607426818.0, 30,   1,  3, 2, 52, -1804345.5, 87,
        #     timestamp,mod, reg,cmd,hk,prt,    nanoTic,S/W,
        #
        # idx:   8     9   10    11    12   13 14    15      16   17
        #     54.8, 46.3, 0.0, 48.7, 45.6, 0.0, 7, 44.0, 4965.0, 0.0]
        #       VM,   RM,  VE,   RE,   RS,   P, E,   FX,      M    A
        #
        # VM:   degC, Vorlauf measured; -127 if sensor not connected
        # RM:   degC, Ruecklauf measured; -127 ...
        # VE:   degC, Vorlauf effectively used for regulation (low-pass)
        # RE:   degC, Ruecklauf effectively used for reg. (low-pass)
        # RS:   degC, Ruecklauf Soll (set) temperature
        # P:    rel. VPos 0-999 0/00,
        # E:    error flags, hex 
        # FX:   nr of fixed position reached,
        # M:    motor on-time, msec,
        # A:    motor Limits reached (Anschlag)
        
        while( l0.find("  ") > -1):
            l0 = l0.replace("  "," ")
        l1 = l0.split(":")
        if len(l1) != 2:
            formCnt += 1
            print(" --- ", l0)
            continue                      # wrong format, next data set
        l10 = l1[0].split(" ")
        if len(l10) != l10Len:
            formCnt += 1
            print(" --- ", l0)
            continue                      # wrong format, next data set
        tst     = time.mktime(time.strptime(l10[0],"%Y%m%d_%H%M%S"))
        modZ    = int( l10[1][0:2], 16 )  # module address, requested from Zentrale
        regZ    = int( l10[1][2:4], 16 )  # regulator nr, requested from Zentrale
        hk      = int( l10[2][2:], 10)

        l20 = l1[1].split(" ")
        cmdM    = int(l20[0][2:4],16)     # command nr answered from module
        modM    = int(l20[0][4:6],16)     # module address answered from module
        regM    = int(l20[0][6],  10)     # regulator nr answered from module
        try:
            prt     = ord(l20[0][7])  # use ascii-number for 'b' or later protocol version -> numpy array needs it
        except Exception as e:
            print(e)
            print(l20)
            prt=0
        tic     = float( (l20[1][1:]) )
        sw      = l20[2]  # S)ummer, W)inter, sometimes '0' or '1'
        if sw == "S" or sw=="W":
            sw = ord(sw)   # replace by ASCII Nr; else numpy array uses strings
        regStat = { 'TST':tst, 'MOD':modM, 'REG':regM, 'CMD':cmdM, \
                    'HK':hk, 'PR':prt, 'TIC':tic, "SW":sw }
        
        # *** check for different module or regulator addresses
        mrFehler=0
        if modZ != modM:
            fehlerMod += 1
            mrFehler=1
        if regZ != regM:
            fehlerReg += 1
            mrFehler=1
        fehlerMR += mrFehler
        
        # values might read e.g. "VM 70.0" or "VM-127.0"
        # -> cannot be separated by " " !!!
        # -> extract values by key-word 
        
        # keyword list, in order to extract the values; 
        # e.g. " M": leading " " is needed to distinguish from "VM"
        #      " " will be removed later
        kwl = ["VM","RM","VE","RE","RS"," P"," E","FX"," M"," A"]  
        l30 = l1[1]
        for kw in kwl:
            pos=l30.find(kw)
            beg=pos+len(kw)
            #while l30[beg]==" ":
            #    beg += 1
            end=l30.find(" ", beg+1)
            if end == -1:
                end = len(l30)  # go to end of string
            if kw==" E":
                val=int(l30[beg:end],16)
            else:
                val=float(l30[beg:end])
            kws = kw.strip()   # remove leading blanks from keyword
            regStat[kws] = val

        if len(regStat) == regStatLen :
            dList.append(regStat)
            datCnt += 1
        else:
            print(" - ",regStat)
            
            pass
            
        # *** check for datasets containing 0s
        zeroEvent=0
        if regStat["VM"] == 0: 
            zeroCntVM +=1
            zeroEvent=1
        if regStat["RM"] == 0: 
            zeroCntRM +=1
            zeroEvent=1
        if regStat["VE"] == 0: 
            zeroCntVE +=1
            zeroEvent=1
        if regStat["RE"] == 0: 
            zeroCntRE +=1
            zeroEvent=1
        if regStat["RS"] == 0: 
            zeroCntRS +=1
            zeroEvent=1
        zeroDsSum += zeroEvent
        dsProblem += zeroEvent + mrFehler

    ldatCnt=0    
    ldat=[]
    for dSet in dList:
        l100=[]
        for key in dSet:
            l100.append( dSet[key] )
        ldat.append(l100)
        ldatCnt += 1
    print("len(ldat)=%d"%(len(ldat)))
    
    #ldat.sort(key=itemgetter(2,4,0))   # sortiere columns 2 (ModulNr), 4(subAdr) und 0(time)
    ldat.sort()
    print("\n* Statistics: Count of datasets with")
    print("* zero value VM:%d(%.1f%%)  RM:%d(%.1f%%)  VE:%d(%.1f%%)  "\
        "RE:%d(%.1f%%)  RS:%d(%.1f%%)"\
        %(zeroCntVM,zeroCntVM/datCnt*100.0,zeroCntRM,zeroCntRM/datCnt*100.0,\
          zeroCntVE,zeroCntVE/datCnt*100.0,zeroCntRE,\
          zeroCntRE/datCnt*100.0,zeroCntRS,zeroCntRS/datCnt*100.0))
    print("* wrong module Nr:%d(%.1f%%)  wrong regulator:%d(%.1f%%)"\
        %(fehlerMod,fehlerMod/datCnt*100.0,fehlerReg,fehlerReg/datCnt*100.0))
    print("* data sets with at least: one 0-value %d(%.1f%%), wrong mod or reg %d(%.1f%%), "\
        "problem of these kinds %d(%.1f%%)"\
        %(zeroDsSum,zeroDsSum/datCnt*100.0,fehlerMR,fehlerMR/datCnt*100.0,\
          dsProblem,dsProblem/datCnt*100.0))
    print("* wrong formatted lines: %d(%.1f%%)"%(formCnt,formCnt/datCnt*100.0))
    print("* lines from file:%d,  accepted:%d"%(lineCnt, datCnt))
    print()
    print("check ldat for string element - bad for array conversion:")
    for row in range(len(ldat)):
        for col in range(len(ldat[0])):
            if type(ldat[row][col]) == 'float' \
            and type(ldat[row][col]) == 'int' :
                print(row,col,ldat[row])
                stop
    adat=np.array(ldat, dtype=float)
    return adat    


def plot_all(ec,filename,adat):
    """ plot all hr2data in one diagram. """
    cm2i = 1.0/2.54  # factor cm to insh
    modules = list( set( [int(x[1]) for x in adat] ) ) # extract all module numbers
    modules.sort()
    nmod = len(modules)
    #a4FormatQ = (29.7*cm2i,21.0*cm2i)
    #a3FormatQ = (42.0*cm2i,29.7*cm2i)
    oFormat   = (80.0*cm2i,nmod*5*cm2i)
    #fig = plt.figure(figsize=a3FormatQ)
    # 4 diagrams in one line
    fig,axs = plt.subplots(int(nmod/2)+1,4,figsize=oFormat)
    print("plot data; mod Nr.= ",end="")
    for mod in modules:
        modIdx = modules.index(mod)
        print("mod=%d --- modIdx=%d"%(mod,modIdx))
        for regNr in [1,3]:
            ri = regNr-1
            # extract all data from mod/regNr
            teil=[]
            for dat in adat:
                if dat[1]==mod and dat[2]==regNr:
                    teil.append(dat)
            #print("teil: mod=%d reg=%d"%(mod,regNr),len(teil), teil)

            # plot data from teil:
            teilA = np.array(teil)
            if teilA.size > 0:
                # *** calculate times and time-axis (x-axis)
                t0        = teilA[0,0]
                ts        = time.localtime( t0 )
                t1        = teilA[ -1,0]
                te        = time.localtime( t1 )
                tSecStart = ts[3]*3600 + ts[4]*60 + ts[5]  # seconds from midnight
                t         = teilA[:,0] - t0 + tSecStart    # seconds from midnight
                th        = t / 3600.0                     # times in hours
                #if mod==modules[0] and regNr==1:                
                # *** set headline and filename
                datimStart = time.strftime('%Y%m%dh%H%M%S',ts)
                datimEnd   = time.strftime('%Y%m%dh%H%M%S',te)
                hostName   = get_hostname()
                pos0 = filename.find("_")+1
                pos1 = filename.find("_", pos0)
                zName      = filename[pos0:pos1]
                titelDiagramm = "HR2_"+zName+"_Mod%02dReg%d_"%(mod,regNr)+datimStart+"-"+datimEnd
                titel = "HR2_"+zName+"_"+datimStart+"-"+datimEnd
                picName = titel +".png"
                # *** prepare plot position
                #diagPos = 2*modIdx+ri+1
                #print("diagPos=",diagPos)
                # ax = plt.subplot(nmod+1,2,diagPos)
                
                # *** extract plot-data (y-axes)
                # index =        0   1   2  3   4    5        6   7       8     9     10    11      12    13  14    15   16   17
                # 18 [1604963488.0,  2,  1, 2,  1, 'b', 28134.8,  1, -127.0, 32.3, -79.0, 38.4,   32.0,  0.0,  2, 21.0, 0.0, 0.0]
                # name=    secEpoc cmd mod HK Reg prot  nanoTic S/W  VLMess   RLM  VLeff  RLeff RLsoll  VPos ERR   Fix    M    A
                # extract data to be plotted:
                vlMess    = teilA[:,8]
                rlMess    = teilA[:,9]
                vlEff     = teilA[:,10]
                rlEff     = teilA[:,11]
                rlSoll    = teilA[:,12]
                vPos      = teilA[:,13] / 10.0
                # *** fit values in diagram
                #TODO replace by function with better algorith to suppress 0-values
                vlMessP   = [max(x,0.0) for x in vlMess]    # remove negative values
                rlMessP   = [max(x,0.0) for x in rlMess]    # remove negative values
                vlEffP    = [max(x,0.0) for x in vlEff]     # remove negative values
                rlEffP    = [max(x,0.0) for x in rlEff]     # remove negative values
                rlSollP   = [max(x,0.0) for x in rlSoll]    # remove negative values
                venPos    = vPos
                # *** plot ALL values
                # four diagrams in one line
                if ri > 0:
                    xDiagPos=1
                else:
                    xDiagPos=0
                xpos = (modIdx % 2) * 2 +  xDiagPos
                ypos = int(modIdx / 2)
                #axs[ypos,xpos].plot(th,vlMessP,"o",linestyle="--", label="%d/%dvlM"%(mod,regNr))
                axs[ypos,xpos].set_title( titelDiagramm )
                axs[ypos,xpos].plot(th,vlMessP,linestyle="--", label="%d/%dvlM"%(mod,regNr))
                axs[ypos,xpos].plot(th,rlMessP,linestyle="-", label="%d/%drlM"%(mod,regNr))
                if mod != 30:
                    axs[ypos,xpos].plot(th,vlEffP, linestyle="--", label="%d/%dvlReg"%(mod,regNr))
                    axs[ypos,xpos].plot(th,rlEffP, linestyle="-", label="%d/%drlReg"%(mod,regNr))
                    axs[ypos,xpos].plot(th,rlSollP,linestyle="-.", label="%d/%drlSoll"%(mod,regNr))
                    axs[ypos,xpos].plot(th,venPos, linestyle=":", label="%d/%dvPosRel"%(mod,regNr))
                
                # *** replace time-tics with hours of the day
                xlocs = axs[ypos,xpos].get_xticks()
                xlabels = axs[ypos,xpos].get_xticks()
                #print("xlocs=",xlocs,"; xlabels=",xlabels)
                xticlabels = [str(t%24) for t in xlocs]
                #plpl axs[ypos,xpos].set_xticklabels(xticlabels)
                
                # *** vertical lines at 00:00
                hourMin = min(xlabels)
                hourMax = max(xlabels)
                vLinePos=[]
                for h in np.arange(hourMin,hourMax):
                    if h%24 == 0:
                        vLinePos.append(h)
                        axs[ypos,xpos].vlines(h,0,100)
                
                axs[ypos,xpos].grid("both")
                axs[ypos,xpos].set_ylabel("degC/%")
                axs[ypos,xpos].legend(fontsize="x-small")
                axs[ypos,xpos].set_xlabel("t / h")

                
    plt.tight_layout()
    outfile = ec["picturePath"] + picName
    plt.savefig(outfile)
    set_eval_message( 1, 1,"graphics file is now in directory %s\n"%(outfile) )

    #plt.show()
    plt.close()
    pass


def select_plot_files( fromDir, toDir, selectStr,  days=2 ):
    ''' select logfiles of form "logHZ-RR_20201121_053503.dat" '''
    # *** select and sort all log-files
    logFileList = glob.glob(fromDir+selectStr)
    logFileList.sort()

    # *** calculate time of log-files
    #     have form: "log/logHZ-RR_20201117_223003.dat"
    fsse = []   # seconds since epoc for files
    for fname in logFileList:
        fname = fname.lstrip(fromDir)  # -> "logHZ-RR_20201117_223003.dat"
        l1 = fname.split("_")
        datum = l1[2]
        zeit  = l1[3].split(".")[0]
        sec   = time.mktime(time.strptime(datum+zeit,"%Y%m%d%H%M%S"))
        print(datum,zeit,sec)
        fsse.append(sec) 
    
    # *** select the newest logfile
    if len(fsse)==0:
        set_eval_message(1,1,"ATT: No files to plot")
        return fsse
        
    lastSec = max(fsse)
    startSec = lastSec - days * 24.0 * 3600.0  # selected days in seconds
    
    # *** find first log file <days> before from last file
    flist = []
    for i in range(len(fsse)):
        print(i,fsse[i],logFileList[i],end=" ")
        if fsse[i] > startSec:
            flist.append(logFileList[i])
            print("appended")
        else:
            print()

    # *** remove old files from destination directory (plot-dir)
    print("delete files in plot dirctory")
    files = glob.glob(toDir+selectStr)
    files.extend( glob.glob(toDir+"sum*.dat"))
    print(files)
    for f in files:
        pass
        print("delete",f)
        os.remove(f)
    
    # *** copy selected files to plot-dir
    print("copy files to plot directory")
    for f in flist:
        print("copy from:",f," to ", toDir)
        shutil.copy2( f, toDir )
        pass
    print("all files copied")        
    set_eval_message(1,1,"plotfiles copied to %s\n"%(toDir))
    return flist



def get_evaluation_config():
    hostname = get_hostname()
    config = configparser.ConfigParser()  # parameters for evaluations
    # *** read Heizkreis configuration data
    #hk = get_hk_param(hostname,"config/heizkreis.ini")
    evalIniPath = "config/"
    evalIniFilename = "hr2_evaluation.ini"
    evalIniFile=evalIniPath+evalIniFilename
    if not os.path.isfile( evalIniFile):
        set_eval_message( 1, 1,"%s not existent, create default\n"%(evalIniFile) )
        pathlib.Path(evalIniPath).mkdir(parents=True, exist_ok=True) 
        print( "config file missing - set default values and make new config file")
        config['version'] = {"rev": "1.0"}
        with open(evalIniFile,"w") as f:
            config.write(f)     # closes file after leaving with:
            f.close()
            
    config.read(evalIniFile)
    if not (hostname in config.sections()):
        config[hostname]={
            "logfilePath"  : "log/", 
            "plotfilePath" : "log/temp_plotlog/",
            "picturePath"  : "Bilder/",
            "selectString" : "nlog*.dat",
        }
        with open(evalIniFile,"w") as f:
            config.write(f)     # closes file after leaving with:
            f.close()
        
    #TODO read to variables ?
    rev = config["version"]["rev"]
    if rev != "1.0":
        print("Wrong version of .ini file - check ini-file")
        eConf=None
    else:
        eConf = {}
        eConf[ "logfilePath" ]  = config[hostname]["logfilePath"]
        eConf[ "plotfilePath" ] = config[hostname]["plotfilePath"]
        eConf[ "picturePath" ]  = config[hostname]["picturePath"]
        eConf[ "selectString" ] = config[hostname]["selectString"]
    return eConf
    

import asyncio

async def run(cmd):
    proc = await asyncio.create_subprocess_shell(
        cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
        )
    
    stdout, stderr = await proc.communicate()
    print("%s exited with %s"%(cmd,proc.returncode))
    if stdout:
        print("stdout=%s"%(stdout.decode()))
    if stderr:
        print("stderr=%s"%(stderr.decode()))




if __name__ == "__main__" :
    
    import logging
    import threading
    
    
    # *** set path to current directory with python scripts
    current_dir = pathlib.Path(__file__).parent
    current_file = pathlib.Path(__file__)
    print(current_dir,current_file)
    os.chdir(current_dir)
    
    # *** start separate thread with window to display progress
    
    
    # *** prepare message file
    set_eval_message( 0 )  # open evaluatioin message file 
    set_eval_message( 8 )  # clear file
    time.sleep(0.5)
    
    #os.system("python3 hr2_show_log_message06.py &")
    asyncio.run(run("python3 hr2_show_log07_message.py &"))

    # *** configuration from file "config/hr2_evaluation.ini"    
    set_eval_message( 1, 1,"read evaluation.ini data\n" )
    ec = get_evaluation_config()
    if ec == None:
        set_eval_message( 1, 1,"  file missing -> setup default file -> check file!\n" )
        exit(1)

    # *** selct time range for log-files, default is 2 days and merge in one file
    days = 2
    set_eval_message( 1, 1,"select files to plot %d days\n"%(days) )
    flist = select_plot_files( ec["logfilePath"], ec["plotfilePath"], ec["selectString"], days ) # copy logfiles to plot
    if flist ==[]:
        print("No files to plot")
    else:
        set_eval_message( 1, 1,"read selected logfiles\n" )
        sumFile = select_log_files( ec["plotfilePath"], ec["selectString"] )
        # read measured values into a big data array
        set_eval_message( 1, 1,"into a big data array\n" )
        adat = read_all_data(ec["plotfilePath"]+sumFile)
        set_eval_message( 1, 1,"plot selected data to a graphics file\n" )
        plot_all(ec,sumFile,adat)
        set_eval_message( 9 )  # close message file
        
        
        #set_eval_message( 1, 1,"" )
    


