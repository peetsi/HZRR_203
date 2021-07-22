#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jan  4 09:54:49 2017

@author: pl
"""

import numpy as np
import matplotlib.pyplot as pl

import time
import sys
import heizkreis_config as hkr_cfg
import rr_parse as parse
import select_log as sellog
from select_log import val


# read in Heizkreis specific parameters
global heizkreis, modules, modTRef, modSendTvor, dtLog, filtFakt
global regActive,TVorlAendWarn,TVorlAendAlarm,TRueckAendWarn,TRueckAendAlarm
global TRueckDeltaPlus,TRueckDeltaMinus,venTravelWarn,venTravelAlarm
hkpar0=hkr_cfg.get_heizkreis_config(0)
heizkreis, modules, modTRef, modSendTvor, dtLog, filtFakt=hkpar0
hkpar1=hkr_cfg.get_heizkreis_config(1)    # read extended information
regActive,TVorlAendWarn,TVorlAendAlarm,TRueckAendWarn,TRueckAendAlarm,\
 TRueckDeltaPlus,TRueckDeltaMinus,venTravelWarn,venTravelAlarm = hkpar1

# local to this module
global av
global tim
global deltat     # time for one timeslice
global datVon, datBis

temp_plot_min = 30
temp_plot_max = 80


# ------- functions

def clip_values_temp( a ):
    n = len(a)
    mini= temp_plot_min
    maxi= temp_plot_max
    for i in range(n):
        if a[i] > maxi : a[i]=maxi
        if a[i] < mini : a[i]=mini
    return a


def extract_time( dtm ):
    t=time.strptime(dtm,"%Y%m%d %H%M%S")
    return t


def time_sec( tstamp ) :
    # tstamp is specially formatted date and time string
    # return time in seconds since epoc from file-timestamp
    #print("  in time_sec(): tstamp=%s"%(tstamp))
    tsec = time.mktime(time.strptime(tstamp,"%Y%m%d_%H%M%S"))
    return tsec


def align_array_len( a, size ):
    # shorten the length of an n x m array to m=size; n is here typ. 3
    n = len(a)
    b=np.zeros((n,size), dtype=np.float32)
    for i in range(n):
        for j in range(size):
            b[i][j] = a[i][j]
    return b




def logfiles2array( flist ) :
    global av
    global tim
    global heizkreis
    global modules
    global modTVor     # Modul Nr. mit zentraler Vor- unf Ruecklauftemperatur
    global val
    global tim
    global deltat
    global nMax

    # count lines in all files
    lineCnt=0
    for fileName in flist:
        file = open(fileName,"r")
        for line in file:
            lineCnt+=1
        file.close()

    modCnt = len(modules)
    conCnt = 3
    # 4 lines for each module are stored; 10 lines as spare buffer
    nMax = int(lineCnt / modCnt / 4 )+10    # number of modules
    valCnt = len(val)                       # values for each module

    #print("%d lines in all selected files"%(lineCnt))
    # big data array:
    av  = np.zeros((modCnt, conCnt, valCnt, nMax), dtype=np.float32)
    tim = np.zeros(nMax, dtype=np.float64)


    fileNr = 0
    idx = 0
    zDateSecOld = 0.0        # start value
    for file in flist:
        fileNr += 1
        print("Lese ein: %d  -  %s"%(fileNr, file))
        logf = open(file,'r')
        for line in logf :
            lineCnt += 1
            l0=line.strip()
            # parse return value is:
            #   (zDateSec,hkr,module,command,control,protVer,modTStamp,summer,
            #    vlm,rlm,vle,rle,rls,ven,err,fix,tmo,tan)
            # or in case of error:
            #   (1,errNr)
            p = parse.rr_parse(l0)
            if len(p) > 2 :         # no error
                try:
                    (zDateSec,hkr,modnr,command,control,protVer,modTStamp,summer,
                    vlm0,rlm0,vle0,rle0,rls0,ven0,err0,fix0,tmo0,tan0) = p
                except Exception as e:
                    print(file,lineCnt,e)
                    continue
                else:
                    if hkr >= 0 :
                        heizkreis = hkr
                    #print("reg=%d "%(reg),end="")

                    # insert values in big data array
                    if ( 1 <= control <= 3) :
                        #print("reg=%d, dt=%f"%(reg,zDateSec))
                        if zDateSecOld == 0.0 :
                            zDateSecOld = zDateSec
                        if zDateSec > zDateSecOld + 60.0:
                            # seconds later all scans are performed
                            # -> new record set
                            idx += 1
                            zDateSecOld = zDateSec
                        
                        # andi : np.where(modules==modnr,1,0)[0]  <- der [0] muss dynamisch eingestellt werden - \
                        #                                            derzeit wird immer index 0 genommen.
                        # Edit andi: eventuell stimmt das doch. ich teste mal kurz.
                        mi = np.where(modules==modnr,1,0)[0]#,0,0) #      module index
                        
                        #andi test: falsch!!!! 
                        #cnt = 1
                        #f = 0
                        #for found in mi:
                        #    if found == 1:
                        #        f = cnt
                        #        break
                        #    cnt += 1

                        #if f == 0: return print("sry but i did not find the regler.")    #not found
                        #mi = f

                        #mi = np.where(modules==modnr)[0][0]  # module index
                        ci = control-1      # controller index 0..3

                        tim[idx]                     = zDateSec
                        av[mi][ci][val["vIdx"]][idx] = idx
                        av[mi][ci][val["vMod"]][idx] = modnr
                        av[mi][ci][val["vSoW"]][idx] = np.float32(summer)
                        av[mi][ci][val["vVlm"]][idx] = vlm0
                        av[mi][ci][val["vRlm"]][idx] = rlm0
                        av[mi][ci][val["vVle"]][idx] = vle0
                        av[mi][ci][val["vRle"]][idx] = rle0
                        av[mi][ci][val["vSol"]][idx] = rls0
                        av[mi][ci][val["vVen"]][idx] = ven0
                    deltat = tim[1] - tim [0]   # sec timeslice


global av

def mean_dev( modAdr, regNr, v ):
    # calculate mean deviation of curve
    # modAdr:   module address
    # regNr:    regulator number 1,2,3
    # v=1:      abs(Vorlauf for evalation - Vorlauf measured)
    # v=2:      (Ruecklauf for eval - Ruecklauf soll )
    global av
    mi = np.where(modules==modAdr)[0][0]  # module index
    ci = regNr-1
    if v == 1:
        x1 = av[mi][ci][val["vVlm"]]
        x2 = av[mi][ci][val["vVle"]]
    elif v == 2:
        x1 = av[mi][ci][val["vSol"]]
        x2 = av[mi][ci][val["vRle"]]
    else:
        x1 = 0
        x2 = 0
    dev = (x2 - x1)
    d = np.mean(dev)
    if -900 < d < 900 :
        pass
    else:
        d = -99.9
    return d


def max_dev( modAdr, regNr, v ):
    # calculate maximum of deviation values
    # modAdr:   module address
    # regNr:    regulator number 1,2,3
    # v=1:      abs(Vorlauf for evalation - Vorlauf measured)
    # v=2:      (Ruecklauf for eval - Ruecklauf soll )
    global av
    mi = np.where(modules==modAdr)[0][0]  # module index
    ci = regNr-1
    if v == 1:
        x1 = av[mi][ci][val["vVlm"]]
        x2 = av[mi][ci][val["vVle"]]
    elif v == 2:
        x1 = av[mi][ci][val["vSol"]]
        x2 = av[mi][ci][val["vRle"]]
    else:
        x1=0.0
        x1=0.0
    maxVal = max(x2 - x1)
    mx = np.mean(maxVal)
    if -900 < mx < 900 :
        pass
    else:
        mx = -99.9
    return mx


def min_dev( modAdr, regNr, v ):
    # calculate minimum of deviation values
    # modAdr:   module address
    # regNr:    regulator number 1,2,3
    # v=1:      abs(Vorlauf for evalation - Vorlauf measured)
    # v=2:      (Ruecklauf for eval - Ruecklauf soll )
    global av
    mi = np.where(modules==modAdr)[0][0]  # module index
    ci = regNr-1
    if v == 1:
        x1 = av[mi][ci][val["vVlm"]]
        x2 = av[mi][ci][val["vVle"]]
    elif v == 2:
        x1 = av[mi][ci][val["vSol"]]
        x2 = av[mi][ci][val["vRle"]]
    else:
        x1=0.0
        x2=0.0
    minVal = min(x2 - x1)
    mn = np.mean(minVal)
    if -900 < mn < 900 :
        pass
    else:
        mn = -99.9
    return mn


def travel( modAdr, regNr, v ):
    # calculate travel of values (changes over time)
    # modAdr:   module address
    # regNr:    regulator number 1,2,3
    # v=1:      Vorlauf Temperatur
    # v=2:      Ruecklauf Temperatur
    # v=3:      Ventilstellung
    global av, tim
    mi = np.where(modules==modAdr)[0][0]  # module index
    ci = regNr-1
    if v == 1:
        x1 = av[mi][ci][val["vVle"]]
    elif v == 2:

        x1 = av[mi][ci][val["vRle"]]
    elif v == 3:
        x1 =  av[mi][ci][val["vVen"]]
    else:
        x1=0.0
    trv = 0.0
    for i in range(1,len(x1)):
        trv += np.abs(x1[i] - x1[i-1])

    startZeit = tim[0]     # sec
    endZeit   = max(tim)   # sec
    dauer     = endZeit - startZeit  # sec
    stunden   = dauer / 3600.0

    return trv/stunden    # travel per hour


from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm,cm
global fontList, fontListSize

white  = (1.0, 1.0, 1.0)
black  = (0.0, 0.0, 0.0)
yellow = (1.0, 1.0 ,0.0)
red    = (0.9, 0.0, 0.1)
orange = (0.9, 0.5, 0.0)
violet = (1.0, 0.0, 0.5)
green  = (0.0, 0.2, 0.2)



def make_stat( moduleSel, datVon, datBis ):
    global fontList, fontListSize, fontListBold, fontListBoldOblique
    pdfName = "Bilder/ReportHK%d_%s-%s.pdf"%(heizkreis,datVon,datBis)
    can = canvas.Canvas(pdfName, pagesize=A4)
    width, height = A4
    margin = 10*mm                        # page margin
    lspc = (height-3*margin) / 20.0 / 4.0 # 22 modules max up to 4 lines each
    cline = height - 2*margin             # startline
    can.translate( margin, margin )           # margin left and bottom
    # Headlines
    can.setFont("Helvetica", 14)
    hs1 = "HZ-RR Heizkreis %d; "%(heizkreis)
    hs2 = "Übersicht von Logdatei %s bis %s"%(datVon,datBis)
    can.drawString(0,cline,hs1+hs2)
    cline -= 2*lspc

    # generate quick overview over all data in moduleSel
    fontList = "Courier"
    #fontListBold = "Courier-Bold"
    fontListBold = "Courier-BoldOblique"
    fontListSize = 10
    can.setFont(fontList, fontListSize)

    s11 = "Mod Reg  Vorlauf               Ruecklauf                 Ventil"
    print(s11)
    can.drawString(0,cline,s11)
    cline -= lspc
    pos=(0,cline)
    for module in moduleSel:
        if module == modTRef :
            continue

#ANDI:  diese zeile wurde angepasst
        mi = np.where(moduleSel==module,1,0)[0]  # module index
        s21 = "%02d       Mitt    Max  Aend.    Min   Mitt    Max  Aend.  Aend."%\
              (module)
        print(s21)
        can.setFillColorRGB( 0,0,0 )
        can.drawString(0,cline,s21)
        cline -= lspc
        pos=(0,cline)
        for reg in range(1,4):
            if reg > regActive[mi]:
                continue
            # 1=Vorlauftemp; 2=Ruecklauftemp.; 3=Ventil
            devVorMean    = mean_dev( module, reg, 1 )
            devVorMax     = max_dev(  module, reg, 1 )
            travVor       = travel(   module, reg, 1 )
            devRueckMean  = mean_dev( module, reg, 2 )
            devRueckMax   = max_dev(  module, reg, 2 )
            devRueckMin   = min_dev(  module, reg, 2 )
            travRueck     = travel(   module, reg, 2 )
            travVen       = travel(   module, reg, 3 )
            s31 = "    %d: %6.1f %6.1f %6.1f %6.1f %6.1f %6.1f %6.1f %6.1f"%\
                  (reg,devVorMean, devVorMax, travVor,\
                   devRueckMin, devRueckMean, devRueckMax, travRueck,\
                   travVen)
            print(s31)
            #can.drawString(0,cline,s31)
            p = (reg,devVorMean, devVorMax, travVor,\
                   devRueckMin, devRueckMean, devRueckMax, travRueck,\
                   travVen)
            line2pdf( can, reg, pos, p )
            cline -= lspc
            pos=(0,cline)
        s41=90*"-"
        print(s41)
        can.setFillColorRGB( 0,0,0 )
        can.drawString(0,cline,s41)
        cline -= lspc
    # Legende:
    hs = "Mitt=Mittelwert; Max=Maximum; Min=Minimum; Aend.=Änderung/h;"
    can.setFillColorRGB( 0,0,0 )
    can.drawString(0,cline,hs)
    cline -= lspc
    pos=(0,cline)
    hs = "Legende zu den Fehlerangaben rechts:"
    can.setFillColorRGB( 0,0,0 )
    can.drawString(0,cline,hs)
    cline -= lspc
    pos=(0,cline)
    hs = "VL=Vorlauf; RL=Rücklauf; VentWeg=Ventil Bewegung; tol=Toleranz; ++! = stark"
    can.drawString(0,cline,hs)
    cline -= lspc
    pos=(0,cline)
    can.showPage()
    can.save()




def line2pdf( can, reg, pos, p ):
    # can   canvas for pdf output
    # p     list with parameters to be printed in a line
    pass
    reg,devVorMean,devVorMax,travVor,devRueckMin, devRueckMean,devRueckMax,\
    travRueck,travVen = p
    text = ""
    hs = "     %d "%(reg)
    can.setFillColorRGB( 0,0,0 )
    can.drawString( pos[0],pos[1], hs )
    pos = (pos[0] + can.stringWidth(hs), pos[1]) # next position
    col, text, pos = draw_value( can, 0, text, devVorMean, pos )
    col, text, pos = draw_value( can, 0, text, devVorMax, pos )
    col, text, pos = draw_value( can, 1, text, travVor, pos )
    col, text, pos = draw_value( can, 0, text, devRueckMin, pos )
    col, text, pos = draw_value( can, 3, text, devRueckMean, pos )
    col, text, pos = draw_value( can, 0, text, devRueckMax, pos )
    col, text, pos = draw_value( can, 2, text, travRueck, pos )
    col, text, pos = draw_value( can, 4, text, travVen, pos )
    can.setFillColorRGB( 0.8,0,0.1 )
    can.drawString( pos[0],pos[1], text )



def draw_value( can, nr, text, value, pos ):
    # use can canvas for pdf output
    # check value concerning limits nr
    # value to be printed
    # pos = (x,y) position where to print
    global fontList, fontListSize
    col    = black
    hs     = "%6.1f "%(value)
    if   nr == 0:
        # no check
        pass
        col = black
    elif nr == 1:
        if value > TVorlAendWarn:
            col = orange
            text+=(" VLÄ")
            can.setFont(fontListBold, fontListSize)
        if value > TVorlAendAlarm:
            col = red
            text+=("++!")
            can.setFont(fontListBold, fontListSize)
    elif nr == 2:
        if value > TRueckAendWarn:
            col = orange
            text+=(" RLÄ")
            can.setFont(fontListBold, fontListSize)
        if value > TRueckAendAlarm:
            col = red
            text+=("++!")
            can.setFont(fontListBold, fontListSize)
    elif nr == 3:
        if value > TRueckDeltaPlus:
            col = red
            text+=(" RL>tol")
            can.setFont(fontListBold, fontListSize)
        if value < TRueckDeltaMinus:
            col = violet
            text+=(" RL<tol")
            can.setFont(fontListBold, fontListSize)
    elif nr == 4:
        if value > venTravelWarn:
            col = orange
            text+=(" VentWegÄ")
            can.setFont(fontListBold, fontListSize)
        if value > venTravelAlarm:
            col = red
            text+=("++!")
            can.setFont(fontListBold, fontListSize)

    can.setFillColorRGB( col[0],col[1],col[2] )
    can.drawString( pos[0],pos[1], hs )
    newpos = (pos[0] + can.stringWidth(hs,fontList,fontListSize), pos[1])
    #print(pos,newpos)
    can.setFont(fontList, fontListSize)
    return col, text, newpos


#regActive,TVorlAendWarn,TVorlAendAlarm,TRueckAendWarn,TRueckAendAlarm,\
# TRueckDeltaPlus,TRueckDeltaMinus,venTravelWarn,venTravelAlarm



def make_diagram( modNr, display, modVlZ, file ) :
    # module        plot a diagram of module
    # display       0: to .pdf file; 1: on screen
    # modVlz        0: keine Zentral-Messung; Mmod. Nr mit Vorlauf zentral
    # file          name of first file needed for start date and time
    global av
    global tim
    global heizkreis
    global val                   # dictionary making indices from variable names
    global nMax
    global modules
    # test
    global tx, vlm, vle, rle, sol, ven, vlz, txMaxIdx
    global ven

    #print("-> make_diagram")
    # calculate time offset from sec-since-epoc for first day
    datum  = time.strftime( "%Y%m%d", time.localtime(tim[0]) )
    datum  = datum + "_000000"
    #print("datum=%s"%(datum))
    toffset = time_sec( datum )
    #print(toffset)
    # time axis and length of valid data
    tx = (tim - toffset) / 3600  # hours; MEZ
    txMaxIdx = 0
    for t in tx:
        if t < 0:
            break
        txMaxIdx += 1
    nMax = txMaxIdx
    datum  = time.strftime( "%Y%m%d", time.localtime(tim[0]) )
    datum  = datum + "_000000"
    #print("datum=%s"%(datum))
    toffset = time_sec( datum )
    #print(toffset)

    # time axis and length of valid data
    tx = (tim - toffset) / 3600  # hours; MEZ

    tx  = np.resize(tx,nMax)

    # extract values from array
    vle = np.zeros((3,nMax),dtype=np.float32)  # Vorlauf evaluation
    rle = np.zeros((3,nMax),dtype=np.float32)  # Ruecklauf evaluation
    sol = np.zeros((3,nMax),dtype=np.float32)  # Sollwerte
    ven = np.zeros((3,nMax),dtype=np.float32)  # Sollwerte
    vlm = np.zeros((3,nMax),dtype=np.float32)  # Vorlauf gemessen
    vlz = np.zeros((3,nMax),dtype=np.float32)  # Vorlauf Zentrale

    # extract applicable values from big data array
    mi = np.where(modules==modNr)[0][0]  # module index
    mz = np.where(modules==modVlZ)[0][0]  # module index
    for ci in range(3):
        #print("umspeichern ci=%d %d daten ..."%(ci,nMax))
        for i in range( nMax ):
            vlm[ci][i] = av[mi][ci][val["vVlm"]][i]
            vle[ci][i] = av[mi][ci][val["vVle"]][i]
            rle[ci][i] = av[mi][ci][val["vRle"]][i]
            sol[ci][i] = av[mi][ci][val["vSol"]][i]
            ven[ci][i] = av[mi][ci][val["vVen"]][i]
            if modNr == modVlZ and ci == 2 :
                # 3. diagram from Zentrall-Modul
                # Zentrale: Vorlauf == av[mi][ci][0][i]
                vlT = av[mi][0] [val["vVle"]] [i]
                rlT = av[mi][0] [val["vRle"]] [i]
                spreizung = vlT - rlT
                ven[ci][i] = spreizung
            if modVlZ != 0 :
                # a module with zentral temperature exists
                vlz[ci][i] = av[mz][ci][val["vVle"]][i]  # show zentrl VLTemp.

    for ci in range(3):
        vle[ci] = clip_values_temp( vle[ci] )
        rle[ci] = clip_values_temp( rle[ci] )
        sol[ci] = clip_values_temp( sol[ci] )
        vlm[ci] = clip_values_temp( vlm[ci] )
        vlz[ci] = clip_values_temp( vlz[ci] )

    if modNr != modVlZ :
        titel=[
               ["HZ-RR: HKr=%d, Mod.=%d, Datum=%s; Strang 1"%(heizkreis,modNr, datum)],
               ["Strang 2"],
               ["Strang 3"]
               ]
    else :
        # special header for module sitting in Zentrale:
        # Strang 3 shows different values
        titel=[
               ["Strang 1: HZ-RR: HKr=%d, Mod.=%d, Datum=%s; "%(heizkreis,modNr, datum)],
               ["Strang 2"],
               ["Zentrale: Spreizung"]
               ]


    fig1 = pl.figure(1, figsize = (18,12))  # inch

    # VENTIL 1
    for i in range(3) :
        #print("Diagramm i=%d ..."%(ci))
        sp = 311 + i
        ax1  = fig1.add_subplot(sp)
        pl.title(titel[i])

        if modVlZ == modNr and i == 2 :
            ax1.set_ylim(0.0, 30.0)
            ax1.plot(tx,ven[i],color="red",linewidth=2,label="Spreizung")
            yticks = [0,10,20,30]
            ax1.set_yticks(yticks)
            ax1.set_ylabel("degC", color="black")
            ax1.minorticks_on()
            ax1.grid(b=True, which='major', color='b', linestyle='-')
            ax1.grid(b=True, which='minor', color='c' )  #, linestyle='--')
            pl.legend(loc="upper left")
        else:
            ax1.plot(tx,vle[i],color="red",linewidth=2,label="vl_e")
            ax1.plot(tx,rle[i],color="blue",linewidth=2,label="rl_e")
            ax1.plot(tx,sol[i],color="cyan",linewidth=2,label="soll")
            if modVlZ != 0 :
                ax1.plot(tx,vlz[i],color="orange",linewidth=1,label="vl_zent.")
            yticks = range( temp_plot_min, temp_plot_max+10, 10 )
            ax1.set_yticks(yticks)
            ax1.set_ylabel("degC", color="black")
            ax1.minorticks_on()
            ax1.grid(b=True, which='major', color='b', linestyle='-')
            ax1.grid(b=True, which='minor', color='c' )  #, linestyle='--')
            pl.legend(loc="upper left")
            # rechte y-Achse
            ax2 = fig1.add_subplot(sp, sharex=ax1, frameon=False)
            ax2.plot(tx,ven[i],"-+",color="green",linewidth=1,label="vent")
            ax2.yaxis.tick_right()
            ax2.yaxis.set_label_position("right")
            ax2.set_yticks([0,20,40,60,80,100])
            ax2.set_ylim(0.0, 100.0)
            ax2.set_ylabel("Ventil %d; ca. %%"%(i+1))
            for tl in ax2.get_yticklabels():
                tl.set_color("green")

    pl.draw()

    time.sleep(0.1)

    #print("file=%ss; fl="%(file),end="")
    fl = file.split("_")
    #print (fl)
    dat = fl[1]
    zeit= fl[2].split(".")[0]

    pl.plot()
    if display == 1:
        print("zeige auf Bildschirm")
        pl.show()
    if display == 0:
        name="Bilder/HK%dMod%d_%s_%s.pdf"%(heizkreis,modNr,dat,zeit)
        print("speichere in Datei",name)
        fig1.savefig( name, bbox_inches="tight" )
    time.sleep(0.1)
    pl.close(fig1)


# ------- select files from date selection





# ----------------
# ----- main -----
# ----------------
global av
global tim
global val
global datVon, datBis
# for debug:
global modul, display, modTVor, fileVon
global x1,x2,dev



def hz_rr_plot( mode, zeitraum, abfragen, module ):
    # mode =
    #  1 : nur Uebersicht
    #  2 : nur Diagramme
    #  3 : Uebersicht und Diagramme
    # zeitraum
    # 'e' : Ende - tu nichts
    # 'L' : letzter Tag
    # 'Z' : letzte zwei Tage
    # Abfragen
    # 'T' : True;  Modul und Ausgabe abfragen
    # 'F' : False; Alle Module verwenden
    # Module: Liste mit  Modulen von denen ein Diagramm erstellt wird
    # nur wirksam, wenn abfragen == 'F'
    # [1,2,5,7] 
    # []        leere Liste -> alle module verwenden

    if abfragen == 'T' :
        print()
        print("="*70)
        print("Auswertung Uebersicht und Diagramme fuer:")
        print("vorhandene Module: ",modules)
        print("Diagramm fuer Modul Nr; 0=alle; e)nde:",end="")
        antw = input()
        if antw == "e" or antw == "E":
            return
        mod = int(antw)
        display = int(input("Diagramm auf 1->Bildschrim-; 0->Datei als .pdf in './Bilder'"))
        print()
        print("-"*70)
        flist = sellog.select_logfiles("N")
        mod = 1
    else:
        if zeitraum in ['E','e','L','l','Z','z']:
            flist  = sellog.select_logfiles(zeitraum)
        else:
            return

        if module == []:
            moduleSel = modules    # alle Module auswerten
        else:
            moduleSel = []
            for m in module:       # Liste vorgegebener Module abarbeiten
                if m in modules:
                    moduleSel.append(m)


    display= 0   # als .pdf Datei ausgeben

    flist.sort()
    fileVon = flist[0]              # erster Dateiname für Überschrift
    logfiles2array( flist )

    datVon = flist[0].split("/")[1].split("logHZ-RR_")[1].split(".dat")[0]
    n=len(flist)-1
    datBis = flist[n].split("/")[1].split("logHZ-RR_")[1].split(".dat")[0]
    if mode > 0 :
        print("Datei von %s bis %s; Module:"%(datVon,datBis), moduleSel)

    if mode==1 or mode==3 :
        make_stat(moduleSel, datVon, datBis)

    if mode== 2 or mode==3:
        for modul in moduleSel:
            make_diagram( modul, display, modTRef, fileVon )


import ast

if __name__ == "__main__" :
    args = sys.argv
    nargs = len(args)
    print(args)
    
    
    
    if nargs == 1 :
        hz_rr_plot(3, 'z', 'F', [] )
    elif nargs == 5 :
        try:
            mode = int(args[1])
            zeitraum = args[2]
            fragen = args[3]
            strModule = ast.literal_eval( args[4] )
            module    = [int(mod) for mod in strModule]    
            print( mode, zeitraum, fragen, module )
            hz_rr_plot( mode, args[2], args[3], module )
        except Exception as e:
            print(e)
            print( mode,args[2],args[3],args[4] )
            stop()
    else:
        print("usage: %s -> standard settings <-> %s 0 z F"%(args[0], args[0]) )
        print("   or: %s {1|2|3} {e|L|z} {T|F} '[]'")
        print(" with: 1==nur Übersicht; 2==nur Diagramme; 3==beides")
        print("       'e'==Ende; 'L'==letzter Tag; 'z'==letzte zwei Tage")
        print("       'T'==Modul auswählen; 'F'==alle Module, nicht fragen")
        print("       '[]' for plotting all modules or ")
        print("       '[1,2,5,8]' a list of modules to plot in string format")
        
        