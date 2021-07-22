#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
Created on Sun Nov 27 21:07:11 2016

@author: pi
"""

import numpy as np
from graphics import *
import usb_ser_b as us
import modbus_b  as mb
import heizkreis_config as hkr_cfg
#import rr_parse as parse
from hr2_variables import *


# ATTENTION:
# insert connected modules in array below
# TODO: read from file if available
#connected_modules = np.array([1,3,8])    # addresses e {1,..,30}
connected_modules = np.array(range(1,21) )   # addresses e {1,..,30}
modules = connected_modules - 1

clickPoint = 0
endButtonCoord=[0,0,0,0]

scrW  = 1000    # pixel; width of whole screen (window)
scrH  =  700    # pixel; height of whole screen (window)
bottom=   30    # pixel; bottom range for legend and button
nboxx =    6    # number of fields horizontally
nboxy =    5    # number of fields vertically
frame =   10    # pixel; external frame to border
dist  =    5    # pixel; distance between fields
nfldx =    4    # number of fields in a box, horizontally
nfldy =    4    # number of fields in a box, vertically

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
#val[0][0][0]= 55.5



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
      txt.setSize(12)
      txt.setStyle('bold')
      txt.draw(win)
      boxTxt.append(txt)
      # column names
      xt = x0 + 2*fldW
      yt = y0 + 1.5*fldH
      pt = Point(xt,yt)
      txt = Text( pt,"T-Vor Rueck    Soll  V.auf")
      txt.setSize(10)
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
        txt.setSize(10)
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
  endButtonText.setSize(12)
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
    legTexts[ix].setSize(10)
    legTexts[ix].draw(win)


#def ping( modAdr ):
# return us.ping(modAdr)

summer      =  "X"
vlm0        = -99.9
rlm0        = -99.9
vle0        = -99.9 
rle0        = -99.9
rls0        = -99.9
ven0        = -99.9
err0        =   0
fix0        = -99.9
tmo0        = -99.9
tan0        =   0
modFwVersion = ""


def get_parameter( modAdr, controller ) :
  us.get_param(modAdr, controller)
  #modFwVersion = us.get_rxText()[pos+5:pos+9]

  # read parameter data
  # global modFwVersion
  # txCmd = mb.wrap_modbus( modAdr, 3, controller, "" )
  # rxCmd = us.txrx_command( txCmd )
  # pos = rxCmd.find("HZ-RR")  
  # modFwVersion=rxCmd[pos+5:pos+9]


def status( modAdr, controller ):
  # get status information from module modAdr and
  # controller; 0 = module status information
  global zDateSec,hkr,modnr,command,control,protVer,modTStamp,summer
  global vlm0,rlm0,vle0,rle0,rls0,ven0,err0,fix0,tmo0,tan0

  try: 
    us.read_stat(modAdr,controller)
  except Exception as e:
    return 1, print("read_stat error:", e)

  #global summer
  zDateSec=time.time()
  hkr=2
  modnr=modAdr
  command=2
  control=controller
  protVer="b"
  modTStamp=float(us.st.rxMillis) / 1000.0
  summer=us.cn2["SN"]
  #  vlm0 = float(us.cn2["VM"]) # wert
  #  rlm0 = float(us.cn2["RM"]) # wert
  #  vle0 = float(us.cn2["VE"]) # wird in anzeige verwendet
  #  rle0 = float(us.cn2["RE"])
  '''
                        " %c VM%5.1f RM%5.1f VE%5.1f " \
                      "RE%5.1f RS%5.1f P%03.0f E%04X " \
                      "FX%d M%.0f A%d", \
                      jz,          
  stat.tv[v] vorlauf temperatur gemessen,     tempVlMeas      
  stat.tvr[v] vorlauf temperatur verwendet    tempVl        
  stat.tr[v] temperatur rücklauf gemessen     tempRlMeas      
  stat.trr[v] temperatur rücklauf verwendet   tempRlLP2    
  stat.trSoll[v] set temperature              tempSoll
  '''
  print( us.cn2)
  stop
  vlm0 = float(us.cn2["VM"]) # wert
  rlm0 = float(us.cn2["RM"]) # wert
  vle0 = float(us.cn2["VE"]) # wird in anzeige verwendet
  rle0 = float(us.cn2["RE"])
  rls0 = float(us.cn2["RS"])
  ven0 = float(us.cn2["PM"])/10.0
  err0 = int  (us.cn4["ER"])
  fix0 = float(us.cn4["FX"])
  tmo0 = float(us.cn4["MT"])
  tan0 = int  (us.cn4["NL"])
  return 0, "no error"



'''
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
      vlm0 = float( hs )
    except Exception as e:
      fehler |= 0x0004
      pass

  if not fehler:
    von = bis+3
    bis = rxCmd.find(' VE' )
    try:
      hs = rxCmd[von:bis]
      rlm0 = float( hs )
    except Exception as e:
      fehler |= 0x0008
      pass

  if not fehler:
    von = bis+3
    bis = rxCmd.find(' RE')
    try:
      hs=rxCmd[von:bis]
      vle0 = float( hs )
    except Exception as e:
      fehler |= 0x0010
      pass

  if not fehler:
    von = bis+3
    bis = rxCmd.find(' RS')
    try:
      hs=rxCmd[von:bis]
      rle0 = float( hs )
    except Exception as e:
      fehler |= 0x0020
      pass

  if not fehler:
    von = bis+3
    bis = rxCmd.find(' P')
    try:
      hs=rxCmd[von:bis]
      rls0 = float( hs )
    except Exception as e:
      fehler |= 0x0040
      pass

  if not fehler:
    von = bis+2
    bis = rxCmd.find(' E')
    try:
      ven0 = float(rxCmd[von:bis])
    except Exception as e:
      fehler |= 0x0080
      pass

  if not fehler:
    von = bis+2
    bis = rxCmd.find(' FX')
    try:
      err0 = int(rxCmd[von:bis])
    except Exception as e:
      fehler |= 0x0100
      pass

  if not fehler:
    von = bis+3
    bis = rxCmd.find(' M')
    try:
      fix0 = int(rxCmd[von:bis])
    except Exception as e:
      fehler |= 0x0200
      pass

  if not fehler:
    von = bis+2
    bis = rxCmd.find(' A')
    try:
      hs=rxCmd[von:bis]
      tmo0 = float(hs)
    except Exception as e:
      fehler |= 0x0400
      pass

  if not fehler:
    von = bis+2
    try:
      hs=rxCmd[von:]
      tan0 = int(hs)
    except Exception as e:
      fehler |= 0x0020
      pass
'''

def scan_all():
  global modFwVersion
  ende = False
  # plpl for modIdx in range(20):
  for modIdx1 in modules:
    modIdx = modIdx1 - 1
    if ende == True:
      break
    modAdr = modIdx+1
    box[modIdx].setFill('orange')                # mark box as active
    #err = us.ser_reset_buffer()
    answer, repeat = us.ping(modAdr)
    if answer == True :
      # ping echo received
      box[modIdx].setFill(color_echo)   # light green
      # get version information; read from parameters of controller 1
      get_parameter( modAdr, 1 )         # read global modFwVersion

      #temporary:
      modFwVersion = "TBD"
      boxTxt[modIdx].setText("Adr.:%s, V.%s"%(str(modIdx+1),modFwVersion))

      
      # fetch status information and display it
      for controller in [1,2,3] :
        conIdx = controller-1
        conAbsIdx = modIdx*4*4 + conIdx
        repeat = 0
        ende = False
        #while repeat < 3 and not ende:
        e = status( modAdr, controller )
        #  if e > 0 :
        #    repeat += 1
        #  else:
        #    ende = True

        for feld in range(4):
          flIdx = conAbsIdx + feld*4

          print ("type()=",type(e),",e=",e)
          if type(e) is tuple: e = e[0]

          if e > 0 :
            # no valid data received - set all grey and blank
            flRec[flIdx].setFill(color_noEcho)
            flVal[flIdx].setText('      ')
          else:
            # values received - set background color and show values
            if summer == "W":
              # winter mode
              #flVal[conAbsIdx+0*4].setText("%5.1f"%(vle0) )
              #flVal[conAbsIdx+1*4].setText("%5.1f"%(rle0) )
              flVal[conAbsIdx+0*4].setText("%5.1f"%(vlm0) )
              flVal[conAbsIdx+1*4].setText("%5.1f"%(rlm0) )
              flVal[conAbsIdx+2*4].setText("%5.1f"%(rls0) )
              flVal[conAbsIdx+3*4].setText("%3.0f%%"%(ven0) )
              if((err0!=0) or (vlm0==0.0) or (rlm0==999.9)) :
                flRec[conAbsIdx+0*4].setFill(color_error)
                flRec[conAbsIdx+1*4].setFill(color_error)
                flRec[conAbsIdx+2*4].setFill(color_error)
                flRec[conAbsIdx+3*4].setFill(color_error)
              else:
                flRec[conAbsIdx+0*4].setFill(color_winter)
                flRec[conAbsIdx+1*4].setFill(color_winter)
                flRec[conAbsIdx+2*4].setFill(color_winter)
                flRec[conAbsIdx+3*4].setFill(color_winter)
            elif summer == "S":
              # summer mode
              #flVal[conAbsIdx+0*4].setText("%5.1f"%(vle0) )
              #flVal[conAbsIdx+1*4].setText("%5.1f"%(0.0) )
              #flVal[conAbsIdx+2*4].setText("%5.1f"%(0.0) )
              flVal[conAbsIdx+0*4].setText("%5.1f"%(vlm0) )
              flVal[conAbsIdx+1*4].setText("%5.1f"%(rlm0) )
              flVal[conAbsIdx+2*4].setText("%5.1f"%(rls0) )
              flVal[conAbsIdx+3*4].setText("%3.0f%%"%(ven0) )
              if((err0!=0) or (vlm0==0.0) or (rlm0==999.9)) :
                flRec[conAbsIdx+0*4].setFill(color_error)
                flRec[conAbsIdx+1*4].setFill(color_error)
                flRec[conAbsIdx+2*4].setFill(color_error)
                flRec[conAbsIdx+3*4].setFill(color_error)
              else:
                flRec[conAbsIdx+0*4].setFill(color_summer)
                flRec[conAbsIdx+1*4].setFill(color_summer)
                flRec[conAbsIdx+2*4].setFill(color_summer)
                flRec[conAbsIdx+3*4].setFill(color_summer)

    else:
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

    ende = 0
    global cp
    cp = win.checkMouse()    # clickPoint
    key= win.checkKey()      # key pressed

    if cp != None :
      print("clickPoint=",cp)
      cpx = cp.getX()
      cpy = cp.getY()
      epc=endButtonCoord
      print("epc=",epc)
      if( (epc[0] < cpx < epc[2]) and epc[3] < cpy < epc[1] ) :
        ende = True
    if key != "" :
      # Taste beendet den Screen
      ende = True
  return ende, print ("no error")


global heizkreis 
#global modules 
global modTVor 
global modSendTvor 
global dtLog 
global filtFakt

us.ser_check()
#us.ser_open()

# get Heizkreis setup data
h = hkr_cfg.get_heizkreis_config()
if len(h) > 5:
    (heizkreis, modules, modTVor, modSendTvor, dtLog, filtFakt) = h
else:
    # some default values
    heizkreis   = 0
    modules     = []
    modTVor     = 0
    modSendTvor = []
    dtLog       = 180    # time interval to log a data set
    filtFakt    = 0.1

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
  ende, printreturn = scan_all()


win.close()
us.ser.close()


