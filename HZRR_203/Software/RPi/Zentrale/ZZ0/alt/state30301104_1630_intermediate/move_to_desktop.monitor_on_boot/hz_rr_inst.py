#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
Created on Sun Nov 27 21:07:11 2016

@author: pi
"""

from graphics import *
import usb_ser as us
import modbus  as mb


clickPoint = 0

def display_all():





    bw = 80
    bh= 80
    frame    =  20
    dist     =  10
    txoff    =  50
    tyoff    =  50
    ww       = 2*frame + 5*dist + 6*bw
    wh       = 2*frame + 5*dist + 6*bh
    rad      = 10

    win = GraphWin("HZ-RR_Install", ww, wh)

    # draw number field 6x5 with numbers from 1...30
    re = []
    txt= []
    ci = []
    for i in range(6) :
      for j in range(5) :
        idx = i*5 + j
        p1x = frame + i*(bw+dist)
        p1y = frame + j*(bh+dist)
        p1 = Point( p1x, p1y )
        p2x = frame + bw + i*(bw+dist)
        p2y = frame + bh + j*(bh+dist)
        p2 = Point( p2x, p2y )
        #print(idx,p1,p2)
        re.append(  Rectangle( p1, p2 ) )
        re[idx].setFill('grey')
        re[idx].draw(win)
        pt = Point(0.5*(p1x+p2x)+rad,0.5*(p1y+p2y)+rad)
        txt.append( Text(pt,str(idx+1)))
        txt[idx].setSize(22)
        txt[idx].setStyle('bold')
        txt[idx].draw(win)
        pc = Point( p1.getX()+20, p1.getY() + 20)
        ci.append( Circle( pc, rad ))
        ci[idx].setFill('grey2')
        ci[idx].draw(win)

    # draw end-button
    ep0x = frame
    ep0y = 5*(bh + dist) + frame
    ep0 = Point( ep0x, ep0y )
    ep1x = frame + bw
    ep1y = frame + 5*dist + 6*bh
    ep1 = Point( ep1x, ep1y )
    endButton = Rectangle( ep0, ep1 )
    endButton.setFill('red')
    endButton.draw(win)
    ept = Point(0.5*(ep0x+ep1x),0.5*(ep0y+ep1y) )
    endButtonText = Text( ept,"ENDE")
    #endButtonText.setSize(22)
    endButtonText.setStyle('bold')
    endButtonText.draw(win)

    # draw legend
    mx = ep1x + dist + rad
    m1 =  Point(mx, ep0y + rad)
    c1 = Circle( m1, rad )
    c1.setFill('cyan')
    c1.draw(win)
    m2 = Point(mx, (ep0y+ep1y)/2 )
    c2 = Circle( m2, rad )
    c2.setFill('grey2')
    c2.draw(win)
    m3 = Point(mx, ep1y - rad)
    c3 = Circle( m3, rad )
    c3.setFill('red')
    c3.draw(win)
    tx = mx + 2*rad + bw/2
    t1s = Point(tx, ep0y + rad)
    t1  = Text( t1s,"long xfer  ok" )
    t1.draw(win)
    t2s = Point(tx, (ep0y+ep1y)/2 )
    t2  = Text( t2s,"not available" )
    t2.draw(win)
    t3s = Point( tx, ep1y - rad)
    t3  = Text( t3s,"long xfer fail" )
    t3.draw(win)

    p1x = frame + 3*(bw+dist)
    p1y = frame + 5*(bh+dist)
    p1 = Point( p1x, p1y )
    p2x = frame + bw + 3*(bw+dist)
    p2y = frame + bh + 5*(bh+dist)
    p2 = Point( p2x, p2y )
    ra = Rectangle( p1, p2 )
    ra.setFill('grey')
    ra.draw(win)
    tap = Point( 0.5*(p1x+p2x),0.5*(p1y+p2y))
    ta = Text( tap,'no echo')
    ta.draw(win)

    p1x = frame + 4*(bw+dist)
    p1y = frame + 5*(bh+dist)
    p1 = Point( p1x, p1y )
    p2x = frame + bw + 4*(bw+dist)
    p2y = frame + bh + 5*(bh+dist)
    p2 = Point( p2x, p2y )
    rb = Rectangle( p1, p2 )
    rb.setFill('orange')
    rb.draw(win)
    tbp = Point( 0.5*(p1x+p2x),0.5*(p1y+p2y))
    tb = Text( tbp,'ping...')
    tb.draw(win)

    p1x = frame + 5*(bw+dist)
    p1y = frame + 5*(bh+dist)
    p1 = Point( p1x, p1y )
    p2x = frame + bw + 5*(bw+dist)
    p2y = frame + bh + 5*(bh+dist)
    p2 = Point( p2x, p2y )
    rc = Rectangle( p1, p2 )
    rc.setFill('green2')
    rc.draw(win)
    tcp = Point( 0.5*(p1x+p2x),0.5*(p1y+p2y))
    tc = Text( tcp,'echo')
    tc.draw(win)



    # scan all modules and change color if active
    modAdr = 1
    ende = False
    while( not ende) :
      modIdx = modAdr-1
      re[modIdx].setFill('orange')
      err = us.ser_reset_buffer()
      txCmd = mb.wrap_modbus( modAdr, 1, 0, "" )
      #print("*** sende: ",txCmd)
      rxCmd = us.txrx_command( txCmd )
      #print('*** empfange: %s'%( rxCmd ) )
      try:
        rxTab = rxCmd.split()
        if rxTab[2] == 'ACK' :
          # fetch a very long message of all controllers
          fehler = 0
          for controller in [1,2,3,4] :
            txCmd = mb.wrap_modbus( modAdr, 3, controller, "" )
            # ??? sende:  b':0103000F440\r\n'
            #print("---sende: ",txCmd)
            rxCmd = us.txrx_command( txCmd )
            #print ("---empfange: ",rxCmd)
            if "HZ-RR" in rxCmd :
              pass
            else:
              fehler += 1
          if fehler == 0 :
            ci[modIdx].setFill('cyan')
          else:
            ci[modIdx].setFill('red')

          re[modIdx].setFill('green2')


        else:
          re[modIdx].setFill('grey')
          ci[modIdx].setFill('grey2')

      except:
        re[modIdx].setFill('grey')
        ci[modIdx].setFill('grey2')
        pass


      modAdr += 1
      if modAdr > 30 :
        modAdr = 1

      global cp
      cp = win.checkMouse()    # clickPoint
      key= win.checkKey()      # key pressed
      if cp != None :
        print("clickPoint=",cp)
        cpx = cp.getX()
        cpy = cp.getY()
        print(ep0x,ep1x,ep0y,ep1y)
        if( ep0x < cpx < ep1x and ep0y < cpy < ep1y ) :
          ende = True
      if key != "" :
        # Taste beendet den Screen
        ende = True

    # end of loop
    win.close()    # Close window when done

us.serial_connect()
us.ser_open()


display_all()
