#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
Created on Sun Nov 27 21:07:11 2016

@author: pi

Displays status info of all connected modules from last log-file 
"""

import numpy as np
from graphics import *
import usb_ser as us
import modbus  as mb
import os
import glob
import time

# ATTENTION:
# insert connected modules in array below
# TODO: read from file if available
#connected_modules = np.array([1,3,8])    # addresses e {1,..,30}
connected_modules = np.array(range(1,19) )   # addresses e {1,..,30}
modules = connected_modules - 1

clickPoint = 0
endButtonCoord=[0,0,0,0]

# RPi screen size 5" and 7" is 800x480 pixel
# max 18 modules in first installation
scrW  =  800    # pixel; width of whole screen (window)
scrH  =  480    # pixel; height of whole screen (window)
bottom=   30    # pixel; bottom range for legend and button
nboxx =    5    # number of fields horizontally
nboxy =    4    # number of fields vertically
frame =   10    # pixel; external frame to border
dist  =    5    # pixel; distance between fields
nfldx =    4    # number of fields in a box, horizontally
nfldy =    4    # number of fields in a box, vertically
fontSmall = 9
fontTitle = 10

boxW = (scrW - 2*frame - (nboxx - 1)*dist ) / nboxx  # pixel
boxH = (scrH-bottom - 2*frame - (nboxy - 1)*dist ) / nboxy  # pixel

fldW = boxW / nfldx
fldH = boxH / (nfldy+2)  # two for headlines

color_winter = '#d0ffff'
color_summer = '#ffe000'
color_error  = '#8f4fcf'
color_noEcho = 'grey'
color_echo   = '#00ff00'
color_ping   = 'orange'

win = GraphWin("HZ-RR_Monitor", scrW, scrH )

stati = []                    # status lines from file
boxP0 = []
boxP1 = []
boxPt = []
box = []
boxTxt = []
flRec  = []
flVal  = []
val=np.ones((30,4,4))        # values to be diaplayed
val=val*(-99.9)              # stands for 'no vlaue'
#for i in range(30):
#  for j in range(4):
#    for k in range(4):
#      val[i][j][k] = k + j*4 + i*4*4 # TEST !!!
val[0][0][0]= 55.5



pval=np.zeros((30,4,4,2))    # text coordinates x/y for values

def display_all():
  global endButtonCoord
  for spalte in range(nboxx) :
    for zeile in range(nboxy) :
      boxIdx = spalte * nboxy + zeile
      x0 = frame + spalte * (boxW + dist)
      y0 = frame + zeile  * (boxH + dist)
      x1 = x0 + boxW
      y1 = y0 + fldH
      boxP0.append( [x0,y0] )
      boxP1.append( [x1,y1] )
      p0 = Point(x0,y0)
      p1 = Point(x1,y1)
      #print("box von (%d,%d) bis (%d,%d), index=%d"%(x0,y0,x1,y1,boxIdx))
      box.append( Rectangle( p0, p1))
      box[boxIdx].setFill('white')
      box[boxIdx].draw(win)

      # frame around whole box
      y1 = y0 + boxH
      p1 = Point( x1, y1 )
      r = Rectangle( p0, p1 )
      r.setWidth(3)
      r.draw(win)

      # box header with module number
      xt = x0 + 2*fldW
      yt = y0 + 0.5*fldH
      pt = Point(xt,yt)
      boxPt.append([xt,yt])
      txt = Text( pt,"Adr.:%s       "%(str(boxIdx+1)) )
      txt.setSize(fontTitle)
      txt.setStyle('bold')
      txt.draw(win)
      boxTxt.append(txt)
      # column names
      xt = x0 + 2*fldW
      yt = y0 + 1.5*fldH
      pt = Point(xt,yt)
      txt = Text( pt,"T-Vor Rueck   Soll  V.auf")
      txt.setSize(fontSmall)
      #txt.setStyle('bold')
      txt.draw(win)
  #print (boxP0)

  inBox = []
  boxIdx = 0
  for b in box :
    # draw interior of a box
    for sp in range(nfldx) :
      for ze in range(nfldy) :
        #flIdx = boxIdx * nboxx * nboxy * sp * nfldy + ze
        flIdx = ze + sp*nfldy + boxIdx*nfldy*nfldx
        x0 = boxP0[boxIdx][0] + sp * fldW
        y0 = boxP0[boxIdx][1] + ze * fldH + 2*fldH
        x1 = x0 + fldW
        y1 = y0 + fldH
        p0 = Point(x0,y0)
        p1 = Point(x1,y1)
        #print("field von (%d,%d) bis (%d,%d), index=%d"%(x0,y0,x1,y1,boxIdx))
        r=Rectangle(p0,p1)
        r.setFill('grey')
        r.draw(win)
        flRec.append(r)
        # display values
        pvx = 0.5*(x0+x1)
        pvy = 0.5*(y0+y1)
        pval[boxIdx][ze][0] = np.array([pvx,pvy])
        pv  = Point(pvx,pvy)
        v=val[boxIdx][ze][sp]
        if v == -99.9 :
          txt = Text( pv, "     " )
        else:
          txt = Text( pv, "%5.1f"%(val[boxIdx][ze][sp]) )
        txt.setSize(fontSmall)
        txt.draw(win)
        flVal.append(txt)
        #print("flIdx=%d, sp=%f, ze=%f, box=%d, p=(%d,%d), val=%f"%(flIdx,sp,ze,boxIdx, pvx,pvy,val[boxIdx][ze-1][sp]))
    boxIdx += 1

  # draw end-button
  ep0x = frame
  ep0y = scrH-frame
  ep0 = Point( ep0x, ep0y )
  ep1x = frame + boxW
  ep1y = scrH-bottom
  endButtonCoord=[ep0x, ep0y, ep1x, ep1y]
  ep1 = Point( ep1x, ep1y )
  endButton = Rectangle( ep0, ep1 )
  endButton.setFill('red')
  endButton.draw(win)
  ept = Point(0.5*(ep0x+ep1x),0.5*(ep0y+ep1y) )
  endButtonText = Text( ept,"ENDE")
  endButtonText.setSize(fontSmall)
  endButtonText.setStyle('bold')
  endButtonText.draw(win)

  # draw legend
  lXstart = ep1x + dist
  dxPix = boxW / 2
  dyPix = bottom - frame

  legTxt=[ "Winter","Sommer","kein Sensor","Ping","Echo OK",
           "kein Echo","kein Ping","","","","",]
  legCol=[ color_winter, color_summer,color_error,color_ping,color_echo,
           color_noEcho,'white','grey','grey','grey','grey']
  lX0=np.array([])
  nLegBox = 10
  for ix in range(nLegBox):
    xnxt = np.array( [lXstart + ix*(dxPix+dist*0.5)] )
    lX0=np.concatenate([lX0,xnxt])
  lX1=lX0 + dxPix
  legBoxes = []
  legTexts = []
  for ix in range(nLegBox):
    p0 = Point(lX0[ix],ep0y)
    p1 = Point(lX1[ix],ep1y)
    legBoxes.append( Rectangle(p0,p1))
    legBoxes[ix].setFill( legCol[ix])
    legBoxes[ix].draw(win)
    pt = Point( lX0[ix]+dxPix*0.5, ep0y - dyPix*0.5)
    legTexts.append( Text( pt, legTxt[ix]))
    legTexts[ix].setSize(fontSmall)
    legTexts[ix].draw(win)


def ping( modAdr ):
  # TODO: repeat up to 3 times; return number of tries
  maxCnt = 3
  repeat = 0
  ready  = 0
  while not ready and repeat < maxCnt :
    txCmd = mb.wrap_modbus( modAdr, 1, 0, "" )   # send ping
    #print("*** sende: ",txCmd)
    rxCmd = us.txrx_command( txCmd )
    #print('*** empfange: %s'%( rxCmd ) )
    if "ACK" in rxCmd :
      ready = 1
    else:
      repeat += 1
  if repeat < maxCnt :
    return True, repeat
  else :
    return False, repeat


summer     =   9
TVorMess   = -99.9
TRueckMess = -99.9
TVorEval   = -99.9
TRueckEval = -99.9
TRueckSoll = -99.9
ventPos    = -99.9
rxErr      =   0
posFixed   = -99.9
tMoTotal   = -99.9
nMotLimit  =   0



def status( rxCmd ):
  # interpret line:
  # 20161212_200732 0504 :0002054a t27795.4  W VM999.9 RM999.9 VE 55.2 \
  # RE-99.9 RS  0.0 P050 E0000 FX0 M0 A0
  global summer
  global TVorMess
  global TRueckMess
  global TVorEval
  global TRueckEval
  global TRueckSoll
  global ventPos
  global rxErr
  global posFixed
  global tMoTotal
  global nMotLimit
  hs = ""

  fehler = 0
  #txCmd = mb.wrap_modbus( modAdr, 2, controller, "" )
  # b':0102400F746\r\n'
  #print("---sende: ",txCmd)
  #rxCmd = us.txrx_command( txCmd )
  # ':0002011a t28968.1  W VM999.9 RM999.9 VE  0.0 RE-99.9 RS  0.0 P050 E0002 FX0 M0 A0 '
  #print ("---empfange: ",rxCmd)
  #if "HZ-RR" in rxCmd :
  #  pass
  #else:
  #  fehler += 1


  if len(rxCmd) < 80 :
    fehler |= 0x0001

  if not fehler :
    if ' W ' in rxCmd :
      summer = 0
    elif ' S ' in rxCmd :
      summer = 1
    else:
      summer = 99
      fehler |= 0x0002

  if not fehler:
    von = rxCmd.find(' VM') + 3
    bis = rxCmd.find(' RM')
    try:
      hs = rxCmd[von:bis]
      TVorMess = float( hs )
    except Exception as e:
      fehler |= 0x0004
      pass

  if not fehler:
    von = bis+3
    bis = rxCmd.find(' VE' )
    try:
      hs = rxCmd[von:bis]
      TRueckMess = float( hs )
    except Exception as e:
      fehler |= 0x0008
      pass

  if not fehler:
    von = bis+3
    bis = rxCmd.find(' RE')
    try:
      hs=rxCmd[von:bis]
      TVorEval = float( hs )
    except Exception as e:
      fehler |= 0x0010
      pass

  if not fehler:
    von = bis+3
    bis = rxCmd.find(' RS')
    try:
      hs=rxCmd[von:bis]
      TRueckEval = float( hs )
    except Exception as e:
      fehler |= 0x0020
      pass

  if not fehler:
    von = bis+3
    bis = rxCmd.find(' P')
    try:
      hs=rxCmd[von:bis]
      TRueckSoll = float( hs )
    except Exception as e:
      fehler |= 0x0040
      pass

  if not fehler:
    von = bis+2
    bis = rxCmd.find(' E')
    try:
      ventPos = float(rxCmd[von:bis])
    except Exception as e:
      fehler |= 0x0080
      pass

  if not fehler:
    von = bis+2
    bis = rxCmd.find(' FX')
    try:
      rxErr = int(rxCmd[von:bis])
    except Exception as e:
      fehler |= 0x0100
      pass

  if not fehler:
    von = bis+3
    bis = rxCmd.find(' M')
    try:
      posFixed = int(rxCmd[von:bis])
    except Exception as e:
      fehler |= 0x0200
      pass

  if not fehler:
    von = bis+2
    bis = rxCmd.find(' A')
    try:
      hs=rxCmd[von:bis]
      tMoTotal = float(hs)
    except Exception as e:
      fehler |= 0x0400
      pass

  if not fehler:
    von = bis+2
    try:
      hs=rxCmd[von:]
      nMotLimit = int(hs)
    except Exception as e:
      fehler |= 0x0020
      pass

  return fehler



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


def read_last_data( datei ) :
  try:
    file = open( datei, "r" )
  except Exception as e:
    print (e)
    return

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
    busy = True
    while busy :
      for line in datei:
        l0=line.strip()
        l1=l0.split()
        tsecLine = time.mktime(time.strptime(l1[0],"%Y%m%d_%H%M%S"))  # time in seconds 
        if tsecLast - tsecLine < 60.0 :               # the last 60 seconds
          print(i,tstamp,l1[0], tsecLast - tsecLine)
          stati.append( l0 )
          i += 1
      if i == 72:
        busy = False
        break
      else :
        time.sleep(10)     # wait seconds to complete transmission of log-program
  file.close()
  


def show_status():
  global cp
  global tsOld
  
  ende = False

  # wait for new data
  pfad = "log/"
  suchname=pfad+"logHZ-RR_*"
  tsOld    = 0.0   # old timestamp
  fileChange = 0
  ticOld = time.time()
  while not fileChange :
    if time.time()-ticOld > 10 :
      # check every 10 seconds for a file change
      ticOld = time.time()
      flist = glob.glob(suchname)
      flist.sort()
      lastFile = flist[len(flist)-1]
      fileChange = file_change( lastFile )
    cp = win.checkMouse()    # clickPoint
    if cp != None :
      #print("clickPoint=",cp)
      cpx = cp.getX()
      cpy = cp.getY()
      epc=endButtonCoord
      #print("epc=",epc)
      if( (epc[0] < cpx < epc[2]) and epc[3] < cpy < epc[1] ) :
        ende = True

    key= win.checkKey()      # key pressed
    if key != "" :
      ende = True
  
  if not ende :
    stati = []
    read_last_data( lastFile )

    box[modIdx].setFill('orange')     # mark box as active
    box[modIdx].setFill(color_echo)   # light green
    boxTxt[modIdx].setText("Adr.:%s"%(str(modIdx+1)))
    # display status information
    for line in stati:
      l0 = line.strip()
      l1 = line.split()
      e = status( l0 )
      modAdr     = int( l1[1][0:2], base = 16 )
      modIdx     = modAdr - 1
      controller = int( l1[1][2:4], base = 16 )
      conIdx = controller - 1
      conAbsIdx = modIdx*4*4 + conIdx

      for feld in range(4):
        flIdx = conAbsIdx + feld*4
        if e > 0 :
          # no valid data received - set all grey and blank
          flRec[flIdx].setFill(color_noEcho)
          flVal[flIdx].setText('      ')
        else:
          # values received - set background color and show values
          if summer == 0:
            # winter mode
            flVal[conAbsIdx+0*4].setText("%5.1f"%(TVorEval) )
            flVal[conAbsIdx+1*4].setText("%5.1f"%(TRueckEval) )
            flVal[conAbsIdx+2*4].setText("%5.1f"%(TRueckSoll) )
            flVal[conAbsIdx+3*4].setText("%3.0f%%"%(ventPos) )
            if((rxErr!=0) or (TVorEval==0.0) or (TRueckMess==999.9)) :
              flRec[conAbsIdx+0*4].setFill(color_error)
              flRec[conAbsIdx+1*4].setFill(color_error)
              flRec[conAbsIdx+2*4].setFill(color_error)
              flRec[conAbsIdx+3*4].setFill(color_error)
            else:
              flRec[conAbsIdx+0*4].setFill(color_winter)
              flRec[conAbsIdx+1*4].setFill(color_winter)
              flRec[conAbsIdx+2*4].setFill(color_winter)
              flRec[conAbsIdx+3*4].setFill(color_winter)
          elif summer == 1:
            # summer mode
            flVal[conAbsIdx+0*4].setText("%5.1f"%(TVorEval) )
            flVal[conAbsIdx+1*4].setText("%5.1f"%(0.0) )
            flVal[conAbsIdx+2*4].setText("%5.1f"%(0.0) )
            flVal[conAbsIdx+3*4].setText("%3.0f%%"%(ventPos) )
            if((rxErr!=0) or (TVorEval==0.0) or (TRueckMess==999.9)) :
              flRec[conAbsIdx+0*4].setFill(color_error)
              flRec[conAbsIdx+1*4].setFill(color_error)
              flRec[conAbsIdx+2*4].setFill(color_error)
              flRec[conAbsIdx+3*4].setFill(color_error)
            else:
              flRec[conAbsIdx+0*4].setFill(color_summer)
              flRec[conAbsIdx+1*4].setFill(color_summer)
              flRec[conAbsIdx+2*4].setFill(color_summer)
              flRec[conAbsIdx+3*4].setFill(color_summer)
      '''
      # no data stored
      # no echo
      box[modIdx].setFill(color_noEcho)
      boxTxt[modIdx].setText("Adr.:%s         "%(str(modIdx+1)))
      for controller in [1,2,3,4] :
        conIdx = controller-1
        conAbsIdx = modIdx*4*4 + conIdx
        for feld in range(4):
          flIdx = conAbsIdx + feld*4
          # no valid data received - set all grey and blank
          flRec[flIdx].setFill(color_noEcho)
          flVal[flIdx].setText('      ')
      '''

  return ende



try:
  display_all()
except Exception as e:
  print("Fehler %s"%(e))
  #win.getMouse() # Pause to view result
  #win.close()
else:
  pass
  # TODO remove
  #win.getMouse() # Pause to view result
  #win.close()    # Close window when done



ende = 0
while not ende:
  ende = show_status()


win.close()


