#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
Created on Sun Nov 27 21:07:11 2016

@author: pl
"""

import time
import numpy as np
from graphics import *
import usb_ser_c as us
import modbus_b  as mb
import heizkreis_config as hkr_cfg
from hr2_variables_b import *

clickPoint = 0

global endButtonCoord
endButtonCoord=[0,0,0,0]

# *** defined sizes for graphics
scrW  = 1000    # pixel; width of whole screen (window)
scrH  =  700    # pixel; height of whole screen (window)
bottom=   30    # pixel; bottom range for legend and button
# distances to the whole frame and of boxes to each other
frame =   10    # pixel; external frame to border
dist  =    5    # pixel; distance between boxes
# a box contains status data from a module:
nboxx =    6    # number of boxes horizontally
nboxy =    5    # number of boxes vertically
# number of data fields in x- and y direction
nfldx =    4    # number of fields in a box, horizontally
nfldy =    3    # number of fields in a box, vertically = nr of controllers

# *** calculated sized from data above:
# size of a module box showing the status of a module
boxW = (scrW - 2*frame - (nboxx - 1)*dist ) / nboxx  # pixel
boxH = (scrH-bottom - 2*frame - (nboxy - 1)*dist ) / nboxy  # pixel
# size of a data field inside a module box
fldW = boxW / nfldx
fldH = boxH / (nfldy+2)  # two for headlines

color_backgnd= '#666666'
color_box    = '#555555'
color_box_head = '#cccccc'
color_winter = '#d0ffff'
color_summer = '#ffe000'
color_error  = '#8f4fcf'
color_noEcho = 'grey'
color_echo   = '#00ff00'
color_ping   = 'orange'


global heizkreis 
global modules 
global modTVor 
global modSendTvor 
global dtLog 
global filtFakt


# get Heizkreis setup data
def get_heizkreis_data():
    h = hkr_cfg.get_heizkreis_config()
    if len(h) > 5:
        (heizkreis, modules, modTVor, modSendTvor, dtLog, filtFakt) = h
    else:
        # some default values
        print("using default values for Heizkreis data")
        heizkreis   = 0
        modules     = []
        modTVor     = 0
        modSendTvor = []
        dtLog       = 180    # time interval to log a data set
        filtFakt    = 0.1

def show_module_box( modNr ):
    # module boxes are arranged in
    # nboxx columns and
    # nboxy rows
    # count increments from top to bottom in the leftmost column
    # and continues in the next column
    #print("nbox x=%d y=%d"%(nboxx,nboxy))
    modIdx = modNr - 1
    boxIdxY = (modIdx % nboxy)
    boxIdxX = int( modIdx / nboxy )
    #print("ModNr=%d boxIdxX=%d, boxIdxY=%d"%(modNr,boxIdxX,boxIdxY))
    
    # *** plot whole box
    x0 = frame + boxIdxX * (boxW + dist)
    y0 = frame + boxIdxY * (boxH + dist)
    x1 = x0 + boxW
    y1 = y0 + boxH
    box = Rectangle( Point(x0,y0), Point(x1,y1) )
    box.setFill(color_box)
    box.draw(win)

    # *** plot headline 1
    x0 = x0 + 1
    y0 = y0 + 1
    x1 = x1 - 1
    y1 = y0 + fldH - 2
    box = Rectangle( Point(x0,y0), Point(x1,y1) )
    box.setFill(color_box_head)
    box.draw(win)

    xt = x0 + 2*fldW
    yt = y0 + 0.5*fldH
    pt = Point(xt,yt)
    txt = Text( pt,"Mod%d  "%(modNr) )
    txt.setSize(12)
    txt.setStyle('bold')
    txt.draw(win)

    # *** plot headline 2
    y0 = y1 + 2
    y1 = y1 +fldH
    box = Rectangle( Point(x0,y0), Point(x1,y1) )
    box.setFill(color_box_head)
    box.draw(win)
    # column names
    xt = x0 + 2*fldW
    yt = y0 + 0.5*fldH
    txt = Text( Point(xt,yt), "T-Vor Rueck    Soll  V.auf")
    txt.setSize(10)
    #txt.setStyle('bold')
    txt.draw(win)



def draw_bottom_line():
    # *** draw end-button
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

    # *** draw legend
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






# show whole window
win = GraphWin("HR2 - Monitor Rev.01a", scrW, scrH )
win.setBackground(color_backgnd)
draw_bottom_line()



show_module_box(1)
show_module_box(2)
show_module_box(6)
show_module_box(10)
show_module_box(15)
show_module_box(30)

#stoptime = time.time() + 10
#while tmie.time < stoptime:
#    # hier windows ende Befehl einfügen
#    pass

time.sleep(10)
win.close()
#us.ser.close()


