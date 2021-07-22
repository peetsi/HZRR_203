#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
Created on 2020.10.05 

show draft values from Annette-Kollwitz-Anger installation of HZRR-200

@author: pl
"""




import glob
import time
import datetime
from tkinter.constants import E
import numpy as np
import matplotlib.pyplot as plt
import time
import sys
from operator import itemgetter

import rr_parse as parse
import hz_rr_config as cg
import hz_rr_debug as debg
dbg = debg.Debug(1)



def select_log_file(custom_sel=0):

    logonusb = cg.conf_obj.r('system','logPlotPath_logOnUsb',       True)
    path     = cg.conf_obj.r('system','logPlotPath_logFolder_linux',    '/home/pi/Desktop/Monitor/PYTHONUSB/log/plotlog/') if cg.conf_obj.islinux() else cg.conf_obj.r('system','logPlotPath_logFolder_win',    'D:\\coding\\move_to_desktop.monitor_on_boot\\log\\plotlog\\')
    if logonusb:
        path = cg.conf_obj.r('system','logPlotPath_logFolder_usb_l','/media/pi/PYTHONUSB/move_to_desktop.monitor_on_boot/log/plotlog/') if cg.conf_obj.islinux() else cg.conf_obj.r('system','logPlotPath_logFolder_usb_w',    'D:\\coding\\move_to_desktop.monitor_on_boot\\log\\plotlog\\')
    dbg.m("path:",path,cdb=1)

    flist = glob.glob(path+"log*.dat")
    flist.sort()
    fileNr=0
    dbg.m("0  -  Beenden")
    for file in flist:
        fileNr += 1
        dbg.m("%d  -  %s"%(fileNr, file))
    dbg.m("99 -  Alle Dateien in eine Datei")

    if custom_sel != 0:
        fileIndex = custom_sel
    else:
        fileIndex = int(input("Wahl ")) - 1

    #fileIndex = 1
    if len(flist) == 0 or fileIndex==0 :
        dbg.m( "Keine Log-Dateien gefunden" )
        return None

    elif fileIndex==99-1:
        # *** concatenate all files of form:
        #     "ZZ1_AKA7u9/log/logHZ-RR_20201019_000958.dat"
        #     "ZZ1_AKA7u9/log/logHZ-RR_20201019_053904.dat"
        #     "ZZ1_AKA7u9/log/logHZ-RR_20201019_092505.dat"
        von=flist[0].split("/")[2][9:24]
        bis=flist[-1].split("/")[2][9:24]
        dbg.m("Verbinde dateien von %s bis %s"%(von,bis))
        dbg.m("Datei von=",von)
        dbg.m("Datei bis=",bis)
        fileName = path+"/sumHZ-RR_"+von+"-"+bis+".dat"
        dbg.m(fileName)
        fout=open(fileName,"w+")
        rzeile=0
        wzeile=0
        for file in flist:
            #dbg.m("add file:",file," ")
            fin=open(file,"r")
            for line in fin:
                rzeile+=1
                #dbg.m(".")
                if len(line) >100:
                    wzeile+=1
                    fout.write(line)
        fout.close()
        dbg.m("%d Zeilen gelesen, %d Zeilen geschrieben"%(rzeile,wzeile))

    # extract date and time from selected file plpl
    # "logHZ-RR_20161228_043534.dat"  (typical filename)
    else:
        fileName = flist[fileIndex]

    return (path,fileName)


def runme(x=0):
    
    try:
        args = sys.argv
        nargs = len(args)
        dbg.m(args)


        # *** read data from file to array
        try:
            path, fileName  = select_log_file(x)
        except Exception as e:
            dbg.m("sorry but no log files could been found",cdb=1)
            return 1

        dbg.m(50*"-")
        dbg.m("Lese ein: %s"%(fileName))
        logf = open(fileName,'r')
        lineCnt=0
        allDat=[]
        for line in logf :
            lineCnt += 1
            l0=line.strip()
            #dbg.m(l0)
            # parse return value is:
            #   (zDateSec,hkr,module,command,control,protVer,modTStamp,summer,
            #    vlm,rlm,vle,rle,rls,ven,err,fix,tmo,tan)
            # or in case of error:
            #   (1,errNr)
            #dbg.m(l0)
            # [1604985134.0, 2, 1, 2, 2, 'b', 49778.1, 1, 70.0, 40.0, 70.0, 40.0, 0.0, 0.0, 4, 20.0, 0.0, 0.0]
            p = list( parse.rr_parse(l0) )
            #dbg.m(lineCnt, p)
            l = len(p)
            if l > 2:
                #dbg.m(l,p)
                # index =        0  1   2  3   4    5        6   7       8     9     10    11      12    13  14    15   16   17
                # 18 [1604963488.0, 2,  1, 2,  1, 'b', 28134.8,  1, -127.0, 32.3, -79.0, 38.4,   32.0,  0.0,  2, 21.0, 0.0, 0.0]
                # name=    secEpoc HK mod HK Reg prot   tstamp S/W  VLMess   RLM  VLeff  RLeff RLsoll  VPos ERR   Fix    M    A
                # VPos: 0-999, Fix: fixed position reached, M: motor on-time, A: motor Limits reached (Anschlag)
                allDat.append(p)
            if lineCnt > 10:
                pass
                # break   # for debug only
    

        allDat.sort(key=itemgetter(2,4,0))   # sortiere columns 2 (ModulNr), 4(subAdr) und 0(time)
        tvon=allDat[0][0]    # time of first data set
        tbis=allDat[-1][0]   # time of last data set
        dauer=tbis-tvon
        modules = [ allDat[n][2] for n in range(len(allDat)) ]
        nModules= modules.count(30)   # how often module nr 30 appears
        dbg.m("tvon=%d tbis=%d dauer=%dsec "%(tvon,tbis, dauer))
        sampleTime = dauer/ lineCnt
        dbg.m("average sampleTime=%f "%((sampleTime)))
        modCnt = len(set(modules))  # number of different modules
        logInterval = sampleTime * modCnt
        dbg.m("logInterval=%.1f "%(logInterval))
        dbg.m("len(allDat)=",len(allDat))

        #for p in allDat:
        #    if p[2]==1 and p[4]==1:
        #        dbg.m(p)

        # "20201002_092636 0401 HK2 :0002041b t85.0 0 VM-127.0 RM 41.7 VE 70.0 RE 40.0 RS  0.0 P107 E0000 FX41 M43 A1"
        # [1601899779.0, 2, 1, 2, 1, 'b', 265783.1, 0, -127.0, 38.2, 70.0, 38.4, 44.0, 86.0, 2, 20.0, 669.0, 27.0]

        # 20201111_124458 0201 HK2 :0002021b t159706.8 W VM-127.0 RM 24.2 VE 54.0 RE 31.9 RS 44.2 P208 E0006 FX20 M71 A1

        # *** sort plot-data into a new array

        allPlotData = []
        dbg.m("extract plot data; module Nr.:")
        
        for mod in range(1,31):
            dbg.m(mod)
            regData = []
            for reg in [1,3]:    # use only regulagtor 1 and 3 (index 0 and 2)
                ri = reg-1

                teil = []
                for x in allDat:
                    # collect all values of a module and a regulator
                    if x[2]==mod and x[4]==reg:
                        teil.append(x)
                if teil==[]:
                    continue
                else:
                    # extract values from teil-list
                    vml=[]  # vorlauf gemessen
                    rml=[]  # ruecklauf gemessen
                    rll=[]  # vorlauf verwendet
                    vll=[]  # ruecklauf verwendet
                    sol=[]  # sollwert
                    pll=[]  # prozent rel. Ventilstellung
                    for l0 in teil:
                        #dbg.m(l0)
                        vm=l0[8]        # Vorlauf temperature measured
                        #dbg.m("vm=",vm)
                        vml.append(vm)
                        rm=l0[9]        # Ruecklauf temp. measured
                        rml.append(rm)
                        vl=l0[10]       # effective Vorlauf temp / not defined
                        vll.append(vl)
                        rl=l0[11]       # effective Ruecklauf temp.
                        rll.append(rl)
                        so=l0[12]       # Ruecklauf Soll temp.
                        sol.append(so)
                        pl=l0[13]       # valve position
                        pll.append(pl/10.0)
                    al = len(rll)
                    regData.append([reg,vml,rml,vll,rll,sol,pll])
        
            if len(regData) > 0 :
                allPlotData.append([mod,regData])
        dbg.m()
        

        nPlots = len(allPlotData)
        nPlotPoints = []
        dbg.m("points to plot:")
        for i in range(nPlots) :
            k = len(allPlotData[i][1][0][1])
            dbg.m("m%d:%d; "%(i,k))
            nPlotPoints.append( k )
        dbg.m()

        dbg.m("nPlots=",nPlots)
        #dbg.m("nPlotPoints=",nPlotPoints)


        # *** plot

        lastModIdx = len(allPlotData) -1    # the central module Nr.30 is always the last module
        fig = plt.figure(figsize=(8,nPlots*3))
        dbg.m("plot data; mod Nr.= ")
        for pl in range(nPlots):
            ax = plt.subplot(nPlots,1,pl+1)
            if pl==0:
                datims=datetime.datetime.fromtimestamp(tvon).strftime('%Y-%m-%d %H:%M:%S')
                plt.title(fileName+"   "+datims)
            mod = allPlotData[pl][0]
            dbg.m(mod)
            for ri in [0,1]:
                reg=allPlotData[pl][1][ri][0]  # regulator nr
                vml=allPlotData[pl][1][ri][1]  # vorlauf measured 
                if vml[0] < 0 :    # -127 wenn kein Regler angeschlossen ist
                    vml = allPlotData[lastModIdx][1][ri][1]    # central VL temperature von Modul Nr. 30
                tl = [t for t in range(len(vml)) ]           # use length of original vector size
                rml=allPlotData[pl][1][ri][2]  # ruecklauf measured
                vll=allPlotData[pl][1][ri][3]  # effectively used Vorlauf temp.; not may sweep due to filtering -> remove lowpass from filter
                rll=allPlotData[pl][1][ri][4]  # effectively used Ruecklauf temp.; after low-pass filter; remove filter factor
                sol=allPlotData[pl][1][ri][5]  # recklauf set value (Sollwert)
                pll=allPlotData[pl][1][ri][6]  # valve Position 0...999; 0.0...100%
                
                # make same vector length
                plv  = [tl,vml,rml,vll,rll,sol,pll]    # list of plot-vectors
                lplv = [len(pv) for pv in plv]         # list with length of each plot-vector
                #dbg.m("lplv=",lplv)
                lv = min(lplv)                         # minimum length of plot vectors
                for i in range(len(plv)):
                    while len(plv[i]) > lv:
                        plv[i].pop()
                    #dbg.m(len(plv[i]))
                lplv1 = [len(pv) for pv in plv]         # list with length of each plot-vector
                #dbg.m("lplv1=",lplv1)
                
                intervall = dauer / nPlotPoints[ri]
                #dbg.m("tonv=%d tbis=%d, dauer=%.2fh, sampleTime=%.1fsec, intervall=%.2f"%(tvon,tbis,dauer/3600.0,sampleTime,intervall))
                
                t  = [t0 * intervall / 3600.0 for t0 in tl]   # in hours
                if mod != 30:
                    if ri==0:
                        ax.plot(t,vml,linestyle=(0,(1,3)), label="mod%dVL_r%d"%(mod,reg))
                    ax.plot(t,rll,"-", label="mod%dRL_r%d"%(mod,reg))
                    ax.plot(t,sol,":",label="mod%dSet_r%d"%(mod,reg))
                    ax.plot(t,pll,linestyle=(0,(5,1)), label="mod%dP%d%%"%(mod,reg))
                elif ri==0:  # use values from regulator 1 (index 0) to measure Vor- and Ruecklauf temp.
                    ax.plot(t,rml,"-",label="mod%dRLm_r%d"%(mod,reg))
                    ax.plot(t,vml,":",label="mod%dVLm_r%d"%(mod,reg))
                    break

            ax.grid("both")
            ax.set_xlabel("t / h")
            ax.set_ylabel("degC/%")
            ax.legend(fontsize="x-small")

        fn0 = fileName.split(".")[0]
        fn1 = fn0[fn0.rfind("/")+1:]
        picName = path+"Bilder/"+fn1+".png"
    finally:
        dbg.ru()
        #if picName == None: return
        try:
            plt.tight_layout()
            plt.savefig(picName)
            plt.close()
        except Exception as e:
            dbg.m("exception:",e,cdb=1)
            pass
        return


if __name__ == "__main__" :
    args = sys.argv
    nargs = len(args)
    dbg.m(args)

    runme(99)
    exit(0)
    # *** read data from file to array
    try:
        path, fileName  = select_log_file()
    except Exception as e:
        dbg.m("sorry but no log files could been found",cdb=1)
        exit(1)

    dbg.m(50*"-")
    dbg.m("Lese ein: %s"%(fileName))
    logf = open(fileName,'r')
    lineCnt=0
    allDat=[]
    for line in logf :
        lineCnt += 1
        l0=line.strip()
        #dbg.m(l0)
        # parse return value is:
        #   (zDateSec,hkr,module,command,control,protVer,modTStamp,summer,
        #    vlm,rlm,vle,rle,rls,ven,err,fix,tmo,tan)
        # or in case of error:
        #   (1,errNr)
        #dbg.m(l0)
        # [1604985134.0, 2, 1, 2, 2, 'b', 49778.1, 1, 70.0, 40.0, 70.0, 40.0, 0.0, 0.0, 4, 20.0, 0.0, 0.0]
        p = list( parse.rr_parse(l0) )
        #dbg.m(lineCnt, p)
        l = len(p)
        if l > 2:
            #dbg.m(l,p)
            # index =        0  1   2  3   4    5        6   7       8     9     10    11      12    13  14    15   16   17
            # 18 [1604963488.0, 2,  1, 2,  1, 'b', 28134.8,  1, -127.0, 32.3, -79.0, 38.4,   32.0,  0.0,  2, 21.0, 0.0, 0.0]
            # name=    secEpoc HK mod HK Reg prot   tstamp S/W  VLMess   RLM  VLeff  RLeff RLsoll  VPos ERR   Fix    M    A
            # VPos: 0-999, Fix: fixed position reached, M: motor on-time, A: motor Limits reached (Anschlag)
            allDat.append(p)
        if lineCnt > 10:
            pass
            # break   # for debug only


    allDat.sort(key=itemgetter(2,4,0))   # sortiere columns 2 (ModulNr), 4(subAdr) und 0(time)
    tvon=allDat[0][0]    # time of first data set
    tbis=allDat[-1][0]   # time of last data set
    dauer=tbis-tvon
    modules = [ allDat[n][2] for n in range(len(allDat)) ]
    nModules= modules.count(30)   # how often module nr 30 appears
    dbg.m("tvon=%d tbis=%d dauer=%dsec "%(tvon,tbis, dauer))
    sampleTime = dauer/ lineCnt
    dbg.m("average sampleTime=%f "%((sampleTime)))
    modCnt = len(set(modules))  # number of different modules
    logInterval = sampleTime * modCnt
    dbg.m("logInterval=%.1f "%(logInterval))
    dbg.m("len(allDat)=",len(allDat))

    #for p in allDat:
    #    if p[2]==1 and p[4]==1:
    #        dbg.m(p)

    # "20201002_092636 0401 HK2 :0002041b t85.0 0 VM-127.0 RM 41.7 VE 70.0 RE 40.0 RS  0.0 P107 E0000 FX41 M43 A1"
    # [1601899779.0, 2, 1, 2, 1, 'b', 265783.1, 0, -127.0, 38.2, 70.0, 38.4, 44.0, 86.0, 2, 20.0, 669.0, 27.0]

    # 20201111_124458 0201 HK2 :0002021b t159706.8 W VM-127.0 RM 24.2 VE 54.0 RE 31.9 RS 44.2 P208 E0006 FX20 M71 A1

    # *** sort plot-data into a new array

    allPlotData = []
    dbg.m("extract plot data; module Nr.:")
    for mod in range(1,31):
        dbg.m(mod)
        regData = []
        for reg in [1,3]:    # use only regulagtor 1 and 3 (index 0 and 2)
            ri = reg-1

            teil = []
            for x in allDat:
                # collect all values of a module and a regulator
                if x[2]==mod and x[4]==reg:
                    teil.append(x)
            if teil==[]:
                continue
            else:
                # extract values from teil-list
                vml=[]  # vorlauf gemessen
                rml=[]  # ruecklauf gemessen
                rll=[]  # vorlauf verwendet
                vll=[]  # ruecklauf verwendet
                sol=[]  # sollwert
                pll=[]  # prozent rel. Ventilstellung
                for l0 in teil:
                    #dbg.m(l0)
                    vm=l0[8]        # Vorlauf temperature measured
                    #dbg.m("vm=",vm)
                    vml.append(vm)
                    rm=l0[9]        # Ruecklauf temp. measured
                    rml.append(rm)
                    vl=l0[10]       # effective Vorlauf temp / not defined
                    vll.append(vl)
                    rl=l0[11]       # effective Ruecklauf temp.
                    rll.append(rl)
                    so=l0[12]       # Ruecklauf Soll temp.
                    sol.append(so)
                    pl=l0[13]       # valve position
                    pll.append(pl/10.0)
                al = len(rll)
                regData.append([reg,vml,rml,vll,rll,sol,pll])
        if len(regData) > 0 :
            allPlotData.append([mod,regData])
    dbg.m()

    nPlots = len(allPlotData)
    nPlotPoints = []
    dbg.m("points to plot:")
    for i in range(nPlots) :
        k = len(allPlotData[i][1][0][1])
        dbg.m("m%d:%d; "%(i,k))
        nPlotPoints.append( k )
    dbg.m()

    dbg.m("nPlots=",nPlots)
    #dbg.m("nPlotPoints=",nPlotPoints)
    # *** plot
    lastModIdx = len(allPlotData) -1    # the central module Nr.30 is always the last module
    fig = plt.figure(figsize=(8,nPlots*3))
    dbg.m("plot data; mod Nr.= ")
    for pl in range(nPlots):
        ax = plt.subplot(nPlots,1,pl+1)
        if pl==0:
            datims=datetime.datetime.fromtimestamp(tvon).strftime('%Y-%m-%d %H:%M:%S')
            plt.title(fileName+"   "+datims)
        mod = allPlotData[pl][0]
        dbg.m(mod)
        for ri in [0,1]:
            reg=allPlotData[pl][1][ri][0]  # regulator nr
            vml=allPlotData[pl][1][ri][1]  # vorlauf measured
            if vml[0] < 0 :    # -127 wenn kein Regler angeschlossen ist
                vml = allPlotData[lastModIdx][1][ri][1]    # central VL temperature von Modul Nr. 30
            tl = [t for t in range(len(vml)) ]           # use length of original vector size
            rml=allPlotData[pl][1][ri][2]  # ruecklauf measured
            vll=allPlotData[pl][1][ri][3]  # effectively used Vorlauf temp.; not may sweep due to filtering -> remove lowpass from filter
            rll=allPlotData[pl][1][ri][4]  # effectively used Ruecklauf temp.; after low-pass filter; remove filter factor
            sol=allPlotData[pl][1][ri][5]  # recklauf set value (Sollwert)
            pll=allPlotData[pl][1][ri][6]  # valve Position 0...999; 0.0...100%
            # make same vector length
            plv  = [tl,vml,rml,vll,rll,sol,pll]    # list of plot-vectors
            lplv = [len(pv) for pv in plv]         # list with length of each plot-vector
            #dbg.m("lplv=",lplv)
            lv = min(lplv)                         # minimum length of plot vectors
            for i in range(len(plv)):
                while len(plv[i]) > lv:
                    plv[i].pop()
                #dbg.m(len(plv[i]))
            lplv1 = [len(pv) for pv in plv]         # list with length of each plot-vector
            #dbg.m("lplv1=",lplv1)
            intervall = dauer / nPlotPoints[ri]
            #dbg.m("tonv=%d tbis=%d, dauer=%.2fh, sampleTime=%.1fsec, intervall=%.2f"%(tvon,tbis,dauer/3600.0,sampleTime,intervall))
            t  = [t0 * intervall / 3600.0 for t0 in tl]   # in hours
            if mod != 30:
                if ri==0:
                    ax.plot(t,vml,linestyle=(0,(1,3)), label="mod%dVL_r%d"%(mod,reg))
                ax.plot(t,rll,"-", label="mod%dRL_r%d"%(mod,reg))
                ax.plot(t,sol,":",label="mod%dSet_r%d"%(mod,reg))
                ax.plot(t,pll,linestyle=(0,(5,1)), label="mod%dP%d%%"%(mod,reg))
            elif ri==0:  # use values from regulator 1 (index 0) to measure Vor- and Ruecklauf temp.
                ax.plot(t,rml,"-",label="mod%dRLm_r%d"%(mod,reg))
                ax.plot(t,vml,":",label="mod%dVLm_r%d"%(mod,reg))
                break

        ax.grid("both")
        ax.set_xlabel("t / h")
        ax.set_ylabel("degC/%")
        ax.legend(fontsize="x-small")

    fn0 = fileName.split(".")[0]
    fn1 = fn0[fn0.rfind("/")+1:]
    picName = path+"Bilder/"+fn1+".png"
    plt.tight_layout()
    plt.savefig(picName) 
    #plt.show()
    plt.close()
