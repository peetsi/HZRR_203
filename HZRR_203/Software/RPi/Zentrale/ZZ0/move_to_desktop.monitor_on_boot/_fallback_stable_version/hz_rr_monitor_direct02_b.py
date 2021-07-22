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
import rr_parse as parse

from hr2_variables import *
import hr2_variables as hrv

import hz_rr_config as cg
import time as ti
import hz_rr_debug as dbeg
import threading as th
import copy
#import hz_rr_log_n as lg

#import mtTkinter



class MonitorDirect():#th.Thread):

  def __init__(self):
    self.dbg = dbeg.Debug(1)
    self.dbg.m("initiating monitor object",cdb=3)
    none=(None,None,None,None,None,None,None,None,None,None,None,None,None,None,None,None,None,None,None,None,None,None,None,None,None,None)
    (self.cp, self.win, self.key, self.ret_mon_q, self.heizkreis, self.modules, self.modTVor, self.modSendTvor, self.dtLog, \
      self.filtFakt, self.modFwVersion, modules, self.endButtonCoord, dbg, modules, self.boxP0, self.boxP1, self.boxPt, self.box, \
        self.boxTxt, self.flRec, self.flVal, self.color_echo, self.boxTxt, self.color_summer, self.color_error) = none

    #self.connected_modules= np.array(range(1,21) )   # addresses e {1,..,30}
    self.modules          = []#self.connected_modules - 1
    self.clickPoint       = 0
    self.endButtonCoord   = [0,0,0,0]
    self.scrW             = 1000    # pixel; width of whole screen (window)
    self.scrH             =  700    # pixel; height of whole screen (window)
    self.bottom           =   30    # pixel; bottom range for legend and button
    self.nboxx            =    6    # number of fields horizontally
    self.nboxy            =    5    # number of fields vertically
    self.frame            =   10    # pixel; external frame to border
    self.dist             =    5    # pixel; distance between fields
    self.nfldx            =    4    # number of fields in a box, horizontally
    self.nfldy            =    4    # number of fields in a box, vertically
    self.boxW             = (self.scrW - 2*self.frame - (self.nboxx - 1)*self.dist ) / self.nboxx  # pixel
    self.boxH             = (self.scrH-self.bottom - 2*self.frame - (self.nboxy - 1)*self.dist ) / self.nboxy  # pixel
    self.fldW             = self.boxW /  self.nfldx
    self.fldH             = self.boxH / (self.nfldy+2)  # two for headlines
    self.color_winter     = '#d0ffff'
    self.color_summer     = '#ffe000'
    self.color_error      = '#cc99ff' #purple 8f4fcf
    self.color_noEcho     = 'grey'
    self.color_echo       = '#00ff00'
    self.color_ping       = 'orange'
    self.__sleep__delay__ = float(cg.conf_obj.r('system','monitorBusRetryDelay'))
    self.title_hostname   = cg.conf_obj.r('system', 'hostPath')
    self.title_name       = cg.conf_obj.r('system', 'name')
    self.title_mon_name   = cg.conf_obj.r('system', 'monitor_name')
    self.title_version    = cg.conf_obj.r('system', 'version')

    if cg.conf_obj.islinux():
      self.title_hostname = self.get_hostname()
    else:
      self.title_hostname = "WINDOWS"

    self.title_mask       = self.title_hostname + " - " + self.title_name + "-" + self.title_mon_name + " v." +self.title_version + " - " + time.strftime("%Y-%m-%d_%H-%M-%S")
    self.box              = []
    self.boxP0            = []
    self.boxP1            = []
    self.boxPt            = []
    self.ebox             = []
    self.boxTxt           = []
    self.flRec            = []
    self.flVal            = []
    self.val              = np.ones((30,4,4))       # values to be diaplayed
    self.val              = self.val*(-99.9)        # stands for 'no vlaue'
    self.pval             = np.zeros((30,4,4,2))    # text coordinates x/y for values
    self.summer           =  "X"
    self.vlm0             = -99.9
    self.rlm0             = -99.9
    self.vle0             = -99.9
    self.rle0             = -99.9
    self.rls0             = -99.9
    self.ven0             = -99.9
    self.err0             =   0
    self.fix0             = -99.9
    self.tmo0             = -99.9
    self.tan0             =   0
    self.modFwVersion     = ""
    self.ret_mon_q        = "ret_mon_q"
    self.win              = ""#GraphWin()
    self.monitor_start    = 0
    self._cn2              = ""
    self._cn4              = ""

  # get hostname of computer
  def get_hostname(self):
      f = open("/etc/hostname","r")
      zzName = f.readline().strip()
      f.close()
      return zzName

  def runme(self):
    self.runme_t()

  def runme_t(self):
    self.dbg.m("starting runme function",cdb=3)

    if self.monitor_start == 0:
      self.monitor_start = 1

      #h = hkr_cfg.get_heizkreis_config()
      #if len(h) > 5:
      #    (self.heizkreis, self.modules, self.modTVor, self.modSendTvor, self.dtLog, self.filtFakt) = h
      #else:
      #    # some default values
      #    self.heizkreis   = 0
      #    self.modules     = []
      #    self.modTVor     = 0
      #    self.modSendTvor = []
      #    self.dtLog       = 180    # time interval to log a data set
      #    self.filtFakt    = 0.1

      try:
        self.dbg.m("starting display_all",cdb=3)
        self.display_all()
      except Exception as e:
        self.dbg.m("Fehler %s"%(e))
        self.monitor_start = 0
        self.dbg.m("monitor closed after %s runs:"%(str(loop)))
        self.win.close()

      #self.monitor_start = 1
      self.dbg.m("monitor started:",self.monitor_start,3)

      ende = 0
      loop = 0
      while not ende:
        time.sleep(0.01)
        loop += 1
        ende, printreturn = self.scan_all()
        self.dbg.m("loop run:",loop,cdb=3)

      self.monitor_start = 0
      self.dbg.m("monitor closed after %s runs:"%(str(loop)))
      self.win.close()

  def display_all(self):
    self.win = GraphWin(self.title_mask , self.scrW, self.scrH )
    print("self.win",self.win)

    h = hkr_cfg.get_heizkreis_config()
    if len(h) > 5:
        (self.heizkreis, self.modules, self.modTVor, self.modSendTvor, self.dtLog, self.filtFakt) = h
    else:
        self.heizkreis   = 0
        self.modules     = []
        self.modTVor     = 0
        self.modSendTvor = []
        self.dtLog       = 180    # time interval to log a data set
        self.filtFakt    = 0.1

    for spalte in range(self.nboxx) :
      for zeile in range(self.nboxy) :
        #self.dbg.m(zeile or spalte in self.modules)
        #if zeile or spalte in self.modules:
          self.boxIdx = spalte * self.nboxy + zeile
          x0 = self.frame + spalte * (self.boxW + self.dist)
          y0 = self.frame + zeile  * (self.boxH + self.dist)
          x1 = x0 + self.boxW
          y1 = y0 + self.fldH
          self.boxP0.append( [x0,y0] )
          self.boxP1.append( [x1,y1] )
          p0 = Point(x0,y0)
          p1 = Point(x1,y1)
          #print("box von (%d,%d) bis (%d,%d), index=%d"%(x0,y0,x1,y1,boxIdx))
          self.box.append( Rectangle( p0, p1))

          if self.boxIdx+1 in self.modules:
            self.box[self.boxIdx].setFill('white')
            self.box[self.boxIdx].draw(self.win)
          #self.dbg.m("box:",self.box,"nboxx",spalte,"/",self.nboxx,"nboxy",zeile,"/",self.nboxy,cdb=2)
          # frame around whole box
          y1 = y0 + self.boxH
          p1 = Point( x1, y1 )
          r = Rectangle( p0, p1 )
          r.setWidth(3)

          if self.boxIdx+1 in self.modules:
            r.draw(self.win)

          # box header with module number
          xt = x0 + 2*self.fldW
          yt = y0 + 0.5*self.fldH
          pt = Point(xt,yt)
          self.boxPt.append([xt,yt])
          txt = Text( pt,"Adr.:%s       "%(str(self.boxIdx+1)) )
          txt.setSize(12)
          txt.setStyle('bold')

          if self.boxIdx+1 in self.modules:
            txt.draw(self.win)

          self.boxTxt.append(txt)
          # column names
          xt = x0 + 2*self.fldW
          yt = y0 + 1.5*self.fldH
          pt = Point(xt,yt)
          txt = Text( pt,"T-Vor Rueck    Soll  V.auf")
          txt.setSize(10)
          #txt.setStyle('bold')

          if self.boxIdx+1 in self.modules:
            txt.draw(self.win)

      #print (boxP0)

    self.inBox = []
    self.boxIdx = 0
    for b in self.box :
      # draw interior of a box
      for sp in range(self.nfldx) :
        for ze in range(self.nfldy) :
          #flIdx = boxIdx * nboxx * nboxy * sp * nfldy + ze
          flIdx = ze + sp*self.nfldy + self.boxIdx*self.nfldy*self.nfldx
          x0 = self.boxP0[self.boxIdx][0] + sp * self.fldW
          y0 = self.boxP0[self.boxIdx][1] + ze * self.fldH + 2*self.fldH
          x1 = x0 + self.fldW
          y1 = y0 + self.fldH
          p0 = Point(x0,y0)
          p1 = Point(x1,y1)
          #print("field von (%d,%d) bis (%d,%d), index=%d"%(x0,y0,x1,y1,boxIdx))
          r=Rectangle(p0,p1)

          if self.boxIdx+1 in self.modules:
            r.setFill('grey')
            r.draw(self.win)

          self.flRec.append(r)
          # display values
          pvx = 0.5*(x0+x1)
          pvy = 0.5*(y0+y1)
          self.pval[self.boxIdx][ze][0] = np.array([pvx,pvy])
          pv  = Point(pvx,pvy)
          v=self.val[self.boxIdx][ze][sp]
          if v == -99.9 :
            txt = Text( pv, "     " )
          else:
            txt = Text( pv, "%5.1f"%(self.val[self.boxIdx][ze][sp]) )

          if self.boxIdx+1 in self.modules:
            txt.setSize(10)
            txt.draw(self.win)

          self.flVal.append(txt)
          #print("flIdx=%d, sp=%f, ze=%f, box=%d, p=(%d,%d), val=%f"%(flIdx,sp,ze,boxIdx, pvx,pvy,val[boxIdx][ze-1][sp]))
      self.boxIdx += 1

    # draw end-button
    ep0x = self.frame
    ep0y = self.scrH-self.frame
    ep0 = Point( ep0x, ep0y )
    ep1x = self.frame + self.boxW
    ep1y = self.scrH-self.bottom
    self.endButtonCoord=[ep0x, ep0y, ep1x, ep1y]
    ep1 = Point( ep1x, ep1y )
    self.endButton = Rectangle( ep0, ep1 )
    self.endButton.setFill('red')
    self.endButton.draw(self.win)
    ept = Point(0.5*(ep0x+ep1x),0.5*(ep0y+ep1y) )
    self.endButtonText = Text( ept,"ENDE")
    self.endButtonText.setSize(12)
    self.endButtonText.setStyle('bold')
    self.endButtonText.draw(self.win)

    # draw legend
    self.lXstart = ep1x + self.dist
    self.dxPix = self.boxW / 2
    self.dyPix = self.bottom - self.frame

    self.legTxt=[ "Winter","Sommer"," ","Ping","Echo OK",
            "kein Echo","kein Ping","","","","",]
    self.legCol=[ self.color_winter, self.color_summer,self.color_error,self.color_ping,self.color_echo,
            self.color_noEcho,'white','grey','grey','grey','grey']
    lX0=np.array([])
    nLegBox = 10
    for ix in range(nLegBox):
      xnxt = np.array( [self.lXstart + ix*(self.dxPix+self.dist*0.5)] )
      lX0=np.concatenate([lX0,xnxt])
    lX1=lX0 + self.dxPix
    legBoxes = []
    legTexts = []
    for ix in range(nLegBox):
      p0 = Point(lX0[ix],ep0y)
      p1 = Point(lX1[ix],ep1y)
      legBoxes.append( Rectangle(p0,p1))
      legBoxes[ix].setFill( self.legCol[ix])
      legBoxes[ix].draw(self.win)

      pt = Point( lX0[ix]+self.dxPix*0.5, ep0y - self.dyPix*0.5)
      legTexts.append( Text( pt, self.legTxt[ix]))
      legTexts[ix].setSize(10)
      legTexts[ix].draw(self.win)
    #self.win.display()

  def __callingThread(self):
    return th.currentThread().getName().upper()

  def monitor_read_stat_queue(self, modAdr,subAdr):
    us.ser_obj.request(("read_stat",modAdr,subAdr,self.ret_mon_q))
    while not us.ser_obj.response_available(self.ret_mon_q):   # wait for answer            # in response_available has to be added a TTL value.
      pass

    r = us.ser_obj.get_response(self.ret_mon_q)
    if r[0] == False:
      self.dbg.m("error getting cn2 and cn4",cdb=2)
      return r
    self._cn2 = copy.deepcopy(us.ser_obj._cn2)
    self._cn4 = copy.deepcopy(us.ser_obj._cn4)

    self.dbg.m("got cn2+cn4 -> deepcopy into mon_obj.cn2/cn4.",cdb=2)
    self.dbg.m("mon_obj.cn2:", self._cn2,cdb=9) # 9 = verbose debug
    self.dbg.m("mon_obj.cn4:", self._cn4,cdb=9) # 9 = verbose debug
    return True

  def monitor_ping_queue(self,modAdr):
    us.ser_obj.request(("ping",modAdr,self.ret_mon_q))
    while not us.ser_obj.response_available(self.ret_mon_q):   # wait for answer            # in response_available has to be added a TTL value.
      pass
    r = us.ser_obj.get_response(self.ret_mon_q)
    if r[0] == False:
      self.dbg.m("error pinging module",cdb=2)
      return r, us.ser_obj.tries_last_ping
    return True, us.ser_obj.tries_last_ping

  def get_parameter(self, modAdr, controller ) :
    us.ser_obj.request(("get_param",modAdr,controller,self.ret_mon_q))
    while not us.ser_obj.response_available(self.ret_mon_q):   # wait for answer            # in response_available has to be added a TTL value.
      pass
    r = us.ser_obj.get_response(self.ret_mon_q)
    if r[0] == False:
      self.dbg.m("error pinging module",cdb=2)
      return r
    return True

  def monitor_get_jumpers_queue(self, modAdr):
    us.ser_obj.request(("get_jumpers",modAdr,self.ret_mon_q))
    while not us.ser_obj.response_available(self.ret_mon_q):   # wait for answer            # in response_available has to be added a TTL value.
      pass
    r = us.ser_obj.get_response(self.ret_mon_q)
    if r[0] == False:
      self.dbg.m("error getting jumpers from module:",modAdr,cdb=2)
      return r
    return True

  def _reset_status(self):
    self.dbg.m("_reset_status: resetting monitor vars",cdb=3)
    self.zDateSec   = 0
    self.hkr        = 0
    self.modnr      = 0
    self.command    = 0
    self.control    = 0
    self.protVer    = ""
    self.modTStamp  = 0
    self.summer     = ""
    self.vlm0       = 0
    self.rlm0       = 0
    self.vle0       = 0
    self.rle0       = 0
    self.rls0       = 0
    self.ven0       = 0
    self.err0       = 0
    self.fix0       = 0
    self.tmo0       = 0
    self.tan0       = 0
    del self._cn2
    del self._cn4

  def status(self, modAdr, controller ):
    # get status information from module modAdr and
    # controller; 0 = module status information
    self._reset_status()
    try:
      x = self.monitor_read_stat_queue(modAdr,controller)
      self.dbg.m("status(",modAdr,",",controller,") = "+ str(x))
    except Exception as e:
      return 1, self.dbg.m("read_stat error:", e, cdb=1)
    if x != True: return 2, self.dbg.m("monitor_read_stat_queue Error", cdb=1)

    #global summer
    self.zDateSec   = time.time()
    self.hkr        = 2
    self.modnr      = modAdr
    self.command    = 2
    self.control    = controller
    self.protVer    = "b"
    self.modTStamp  = float(st.rxMillis) / 1000.0#float(us.st.rxMillis) / 1000.0
    self.summer     = self._cn2["SN"]#us.cn2["SN"]
    '''
                          " %c VM%5.1f RM%5.1f VE%5.1f " \
                        "RE%5.1f RS%5.1f P%03.0f E%04X " \
                        "FX%d M%.0f A%d", \
                        jz,
    stat.tv[v]      vorlauf temperatur gemessen,     tempVlMeas
    stat.tvr[v]     vorlauf temperatur verwendet    tempVl
    stat.tr[v]      temperatur rücklauf gemessen     tempRlMeas
    stat.trr[v]     temperatur rücklauf verwendet   tempRlLP2
    stat.trSoll[v]  set temperature              tempSoll
    '''
    self.vlm0 = float(self._cn2["VM"]) # wert
    self.rlm0 = float(self._cn2["RM"]) # wert
    self.vle0 = float(self._cn2["VE"]) # wird in anzeige verwendet
    self.rle0 = float(self._cn2["RE"])
    self.rls0 = float(self._cn2["RS"])
    self.ven0 = float(self._cn2["PM"])/10.0
    self.err0 = int  (self._cn4["ER"])
    self.fix0 = float(self._cn4["FX"])
    self.tmo0 = float(self._cn4["MT"])
    self.tan0 = int  (self._cn4["NL"])
    return 0, "no error"

  def scan_all(self):
    ende = False
    for modIdx1 in self.modules: # plpl for modIdx in range(20):
      modIdx = modIdx1 - 1
      if ende == True:
        break
      modAdr = modIdx+1
      self.box[modIdx].setFill('orange')                # mark box as active

      answer = self.monitor_ping_queue(modAdr)
      if answer[0] == True :
        ping_tries = answer[1]                      # ping echo received
        self.box[modIdx].setFill(self.color_echo)   # light green
        self.get_parameter( modAdr, 1 )             # get version information; read from parameters of controller 1 read global modFwVersion
        answer = self.monitor_get_jumpers_queue(modAdr)
        if answer == False:
          answer = "err"
          self.dbg.m("monitor_get_jumpers_queue:",answer,cdb=1)
        self.modFwVersion = st.jumpers if answer != "err" else answer #set jumper if possible - otherwise set to err
        self.boxTxt[modIdx].setText("Adr.:%s, V.%02xX P(%s)"%(str(modIdx+1),self.modFwVersion,str(ping_tries)))

        # fetch status information and display it
        for controller in [1,2,3] :
          conIdx = controller-1
          self.conAbsIdx = modIdx*4*4 + conIdx
          ende = False

          e = self.status( modAdr, controller )
          self.dbg.m("mod:",modAdr,"controller:",controller,";e[0]",e[0],";e[0]>0:",e[0] > 0,cdb=3)
          if e[0] > 0 : # error
            for feld in range(4):
              self.flIdx = self.conAbsIdx + feld*4
              self.flRec[self.flIdx].setFill(self.color_noEcho)
              self.flVal[self.flIdx].setText('      ')
          else:
            for feld in range(4):
              self.flIdx = self.conAbsIdx + feld*4
              # values received - set background color and show values
              # store:    0            1              2             3          4       5
              _id =   (   0,           0,              '%5.1f',   '%5.1f',  '%5.1f','%3.0f%%')
              _vals = (self.summer, self.conAbsIdx, _id[2]%(self.vle0),#(self.vlm0),
                                                    _id[3]%(self.rlm0),
                                                    _id[4]%(self.rls0),
                                                    _id[5]%(self.ven0))
              using_color = []
              err_rects = []
              #initialize correct color based on rx value from nano
              for i in range(0,4): #  4 set color per line
                if (_vals[0].lower() == "s"):
                  _uc = self.color_summer
                elif (_vals[0].lower() == "w"):
                  _uc = self.color_winter
                else:
                  _uc = self.color_error
                using_color.append(_uc)
                self.dbg.m("using_color.append(%s)"%(_uc),cdb=9)

              self.dbg.m("pre_check_using_color:",using_color,cdb=9)
              #second selective check an mark a single error field, not the entire line! maybe more visibility?
              if((self.vle0 == 0 or self.vle0 == -127) or (self.rls0==0.0 or self.rls0 == -127) or (self.rlm0==0.0 or self.rlm0==-127)) :
                using_color[0] = self.color_error if (self.vle0 == 0.0 or self.vle0 == -127) else using_color[0]
                using_color[1] = self.color_error if (self.rlm0 == 0.0 or self.rlm0 == -127) else using_color[1]
                using_color[2] = self.color_error if (self.rls0 == 0.0 or self.rls0 == -127) else using_color[2]
                result = all(elem == self.color_error for elem in using_color[:-1])
                if result: using_color[3] = self.color_error
                self.dbg.m("result:",result, "using_color:",using_color,cdb=9)
                #self.dbg.m("SEC_CHECK_ERR] self.vlm0:",self.vlm0,";self.rlm0:",self.rlm0,";self.rls0:",self.rls0,";err_rects:",str(err_rects),cdb=3)

              self.fill_rects   (0,4,using_color) # fill all rects in this run using the using_color - assuming no number is wrong.
              self.box_set_texts(0,4,_vals)

      else:
        # no echo
        self.box[modIdx].setFill(self.color_noEcho)
        self.boxTxt[modIdx].setText("Adr.:%s         "%(str(modIdx+1)))
        for controller in [1,2,3,4] :
          conIdx = controller-1
          conAbsIdx = modIdx*4*4 + conIdx
          for feld in range(4):
            flIdx = conAbsIdx + feld*4
            # no valid data received - set all grey and blank
            self.flRec[flIdx].setFill(self.color_noEcho)
            self.flVal[flIdx].setText('      ')

      # location of the 4 extra boxes
      self.box_set_text( 1, "VE", of = (modIdx*4*4 + -1))
      self.box_set_text( 1, "RM", of = (modIdx*4*4 +  3))
      self.box_set_text( 1, "RS", of = (modIdx*4*4 +  7))
      self.box_set_text( 1, "PM", of = (modIdx*4*4 +  11))


      ende = False
      try:
        self.cp = self.win.checkMouse()    # clickPoint
        self.key= self.win.checkKey()      # key pressed
      except GraphicsError:
        ende = True
        pass

      if self.cp != None :
        self.dbg.m("clickPoint=",self.cp)
        self.cpx = self.cp.getX()
        self.cpy = self.cp.getY()
        self.epc = self.endButtonCoord
        self.dbg.m("epc=",self.epc)
        if( (self.epc[0] < self.cpx < self.epc[2]) and self.epc[3] < self.cpy < self.epc[1] ) :
          ende = True
      if self.key != "" :
        # Taste beendet den Screen
        ende = True
    return ende, 0


  def box_set_texts(self, f:int, t:int, tu:tuple ):
    # store:    0            1              2           3          4          5
    # vals = (self.summer, self.conAbsIdx, self.vlm0, self.rlm0, self.rls0, self.ven0 )
    if len(tu) < 6: # needs to be 6!
      self.dbg.m("set_text error: len(t) < 5:",str(t),cdb=1)
      return 1
    for i in range(f, t):
      self.box_set_text(i,tu[i+2])
    return

  def box_set_text(self, feld, text, of = 0):
    x = self.conAbsIdx if of == 0 else of
    return self.flVal[x+feld*4].setText( text )

  def fill_rects(self, f, t, col:tuple or list):
    i = 0
    for i in range(f,t):
      self.fill_rect(i, col[i] )
      i += 1

  def fill_rect(self, id, col ):
    return self.flRec[self.conAbsIdx+id*4].setFill(col)

mon_obj = MonitorDirect()

if __name__ == "__main__":
  us.ser_obj.ser_check()
  mon_obj.runme()
  pass

