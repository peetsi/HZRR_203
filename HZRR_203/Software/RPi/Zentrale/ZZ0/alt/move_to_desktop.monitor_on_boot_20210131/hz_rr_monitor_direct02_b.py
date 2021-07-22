#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""
Created on Sun Nov 27 21:07:11 2016

@author: pi
"""
import copy
import threading as th

import numpy as np

#import time as ti
#import modbus_b  as mb
#import rr_parse as parse
import hr2_variables as hrv
import hz_rr_config as cg
import hz_rr_debug as dbeg
import usb_ser_b as us
from graphics import *
from hr2_variables import *


class MonitorDirect():#th.Thread):

  def __init__(self):
    self.dbg = dbeg.Debug(1)
    self.dbg.m("initiating monitor object",cdb=3)
    if hasattr(self, "win") == True:
      self.dbg.m("HAS ATTR ?!")
      try:
        self.win.close()
      except Exception as e:
        pass
        #self.dbg.m('__init__(%s): self.win could not been destryoed',cdb=-7)

    none=(None,None,None,None,None,None,None,None,None,None,None,None,None,None,None,None,None,None,None,None,None,None,None)
    (self.cp, self.win, self.key, self.ret_mon_q, self.heizkreis, self.modules, self.modTVor, self.modSendTvor, self.dtLog, \
      self.filtFakt, self.modFwVersion, self.endButtonCoord, self.boxP0, self.boxP1, self.boxPt, self.box, \
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
    self.color_zero       = '#1ac100'
    self.color_error      = '#cc99ff' #purple 8f4fcf
    self.color_noEcho     = 'grey'
    self.color_echo       = '#00ff00'
    self.color_ping       = 'orange'
    self.__sleep__delay__ = float(cg.conf_obj.r('system','monitorBusRetryDelay'))
    self.title_hostname   = cg.conf_obj.r('system', 'hostPath')
    self.title_name       = cg.conf_obj.r('system', 'name')
    self.title_mon_name   = cg.conf_obj.r('system', 'monitor_name')
    self.title_version    = cg.conf_obj.r('system', 'version')
    self.title_hostname   = self.get_hostname() if cg.tb.islinux() else 'WINDOWS'
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
    self.vm_send_mod      = self.modTVor
    self.modFwVersion     = ""
    self.ret_mon_q        = "ret_mon_q"
    self.win              = ""#GraphWin()
    self.monitor_start    = 0
    #self._cn2,self._cn4   = hrv.get_cn('m')
    # debug
    self.special_box_id   = 29
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
      self.monitor_start  = 1
      self.ende           = False
      loop                = False

      try:
        self.dbg.m("starting display_all",cdb=3)
        self.display_all()
      except Exception as e:
        self.dbg.m("Fehler %s"%(e),cdb=-7)
        self.dbg.m("monitor closed after %s runs:"%(str(loop)),cdb=-7)
        self.win.close()
        self.monitor_start = 0
        self.ende = True
      self.dbg.m("monitor started:",self.monitor_start,3)

      while not self.ende:
        time.sleep(0.01)
        loop += 1
        self.ende = self.scan_all()
      self.dbg.m("loop run:",loop,cdb=3)
      self.monitor_start = 0
      self.dbg.m("monitor closed after %s runs:"%(str(loop)))
      self.win.close()

  def display_all(self):
    self.win = GraphWin(self.title_mask , self.scrW, self.scrH )
    print("self.win",self.win)

    h = cg.hkr_obj.get_heizkreis_config()
    if len(h) > 5:
        (self.heizkreis, self.modules, self.modTVor, self.modSendTvor, self.dtLog, self.filtFakt) = h
    else:
        (self.heizkreis, self.modules, self.modTVor, self.modSendT, self.dtLog ,self.filtFakt) =  (0,[],0,[],180,0.1)
    self.vm_send_mod = self.modTVor

    for spalte in range(self.nboxx) :
      #print('+---+')
      for zeile in range(self.nboxy) :
        #self.dbg.m(zeile or spalte in self.modules)
        #if zeile or spalte in self.modules:
        _boxIdx = spalte * self.nboxy + zeile
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
        #_t = str(_boxIdx+1)
        #_x = ('| '+ _t +' |') if (len(_t) < 2) else ('|' + _t + ' |')
        #if (len(_t) >= 3): _x = ('|'+_t+'|')
        #print(_x, end= '')

        if (_boxIdx+1 in self.modules):
        #if (_boxIdx in self.modules or _boxIdx+1 == self.special_box_id):
          self.box[_boxIdx].setFill('white')
          self.box[_boxIdx].draw(self.win)
        #self.dbg.m("box:",self.box,"nboxx",spalte,"/",self.nboxx,"nboxy",zeile,"/",self.nboxy,cdb=2)
        # frame around whole box
        y1 = y0 + self.boxH
        p1 = Point( x1, y1 )
        r = Rectangle( p0, p1 )
        r.setWidth(3)

        if (_boxIdx+1 in self.modules):
        #if (_boxIdx+1 in self.modules or _boxIdx+1 == self.special_box_id):
          r.draw(self.win)

        # box header with module number
        xt = x0 + 2*self.fldW
        yt = y0 + 0.5*self.fldH
        pt = Point(xt,yt)
        self.boxPt.append([xt,yt])
        txt = Text( pt,"Adr.:%s       "%(str(_boxIdx+1)) )
        txt.setSize(12)
        txt.setStyle('bold')

        if (_boxIdx+1 in self.modules):
        #if (_boxIdx in self.modules or _boxIdx+1 == self.special_box_id):
          txt.draw(self.win)

        self.boxTxt.append(txt)
        # column names
        xt = x0 + 2*self.fldW
        yt = y0 + 1.5*self.fldH
        pt = Point(xt,yt)
        txt = Text( pt,"T-Vor Rueck    Soll  V.auf")
        txt.setSize(10)
        #txt.setStyle('bold')

        if (_boxIdx+1 in self.modules):
        #if (_boxIdx in self.modules or _boxIdx+1 == self.special_box_id):
          txt.draw(self.win)
      #print('+---+')
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
    return self.add_mon_queue( ser_bus_work=("read_stat",modAdr,subAdr) )
    #_work         = us.ser_add_work(("read_stat",modAdr,subAdr,self.ret_mon_q))
    #if _work[0] == False: # give back default variables
    #  return False,_work[1]
    #self.dbg.m("monitor_read_stat_queue assigning:",hrv.get_cn('m')[0],"//",hrv.get_cn('m')[1],cdb=3)
    #return True,_work[1]

  def monitor_ping_queue(self,modAdr):
    return self.add_mon_queue( ser_bus_work=("ping",modAdr) )
    #_work         = us.ser_add_work(("ping",modAdr,self.ret_mon_q))
    #if _work[0] == False: # give back default variables
    #  return False,_work[1]
    #self.dbg.m("monitor_ping_queue:",_work[1],cdb=3)
    #return True, us.ser_obj.tries_last_ping

  def get_parameter(self, modAdr, controller ) :
    return self.add_mon_queue( ser_bus_work=("get_param",modAdr,controller) )
    #_work         = us.ser_add_work(("get_param",modAdr,controller,self.ret_mon_q))
    #if _work[0] == False: # give back default variables
    #  return False,_work[1]
    #self.dbg.m("get_parameter:",_work[1],cdb=3)
    #return True, _work[1]

  def monitor_get_jumpers_queue(self, modAdr):
    return self.add_mon_queue( ser_bus_work=("get_jumpers",modAdr) )
    #_work         = us.ser_add_work()
    #if _work[0] == False: # give back default variables
    #  return False,_work[1]
    #self.dbg.m("monitor_get_jumpers_queue:",_work[1],cdb=3)
    #return True, _work[1]

  def add_mon_queue(self, ser_bus_work:tuple):
    _temp = list(ser_bus_work)
    _temp.append(self.ret_mon_q)
    _new_work   = tuple(_temp)
    _work, retv = us.ser_add_work(_new_work,mon_r=True)
    print("_work:",_work)
    print("retv:",retv)
    if _work == False: # give back default variables
      return False,retv[1]
    try:
      #test = tuple(map(str, retv[1].replace('(','').replace(')','').split[',']))
      #print("test:",test[0])
      _r = retv[1].replace('(','').replace(')','').replace("'",'')[:-1].split(", ")
      _r = _r[-1]
    except Exception as e:
      self.dbg.m("add_mon_queue exception:",e,cdb=3)

    self.dbg.m('add_mon_queue:',ser_bus_work[0],":",_r,cdb=3)
    return retv[0], _r



    #us.ser_obj.request(("get_jumpers",modAdr,self.ret_mon_q))
    #while not us.ser_obj.response_available(self.ret_mon_q):   # wait for answer            # in response_available has to be added a TTL value.
    #  pass
    #r = us.ser_obj.get_response(self.ret_mon_q)
    #if r[0] == False:
    #  self.dbg.m("error getting jumpers from module:",modAdr,cdb=2)
    #  return r
    #return True
    #hrv.reset_cn('m')
    #self._cn2, self._cn4=  hrv.get_cn('m')
    #us.ser_obj.request(("ping",modAdr,self.ret_mon_q))
    #while not us.ser_obj.response_available(self.ret_mon_q):   # wait for answer            # in response_available has to be added a TTL value.
    #  pass
    #r = us.ser_obj.get_response(self.ret_mon_q)
    #if r[0] == False:
    #  self.dbg.m("error pinging module",cdb=2)
    #  return r, us.ser_obj.tries_last_ping
    #us.ser_obj.request(("get_param",modAdr,controller,self.ret_mon_q))
    #while not us.ser_obj.response_available(self.ret_mon_q):   # wait for answer            # in response_available has to be added a TTL value.
    #  pass
    #r = us.ser_obj.get_response(self.ret_mon_q)
    #if r[0] == False:
    #  self.dbg.m("error getting paramas module",cdb=2)
    #  return r

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
    hrv.reset_cn('m')

  def status(self, modAdr, controller ):
    # get status information from module modAdr and
    # controller; 0 = module status information
    self._reset_status()
    x,y = "", ""
    try:
      x,y = self.monitor_read_stat_queue(modAdr,controller)
      self.dbg.m("status(",modAdr,",",controller,") = "+ str(x))
    except Exception as e:
      self.dbg.m("read_stat error:", e,"//y:",y, cdb=-7)
      return 1, "read_stat error:"+ e+"//y:"+y
    if x != True:
      self.dbg.m("monitor_read_stat_queue Error:",y, cdb=1)
      return 2, "monitor_read_stat_queue Error:"+y
    _cn2, _cn4 = hrv.get_cn('m')
    self.dbg.m("_cn2",_cn2,cdb=3)
    self.dbg.m("_cn4",_cn4,cdb=3)
    #global summer
    self.zDateSec   = time.time()
    self.hkr        = 2
    self.modnr      = modAdr
    self.command    = 2
    self.control    = controller
    self.protVer    = "b"
    self.modTStamp  = float(st.rxMillis) / 1000.0#float(us.st.rxMillis) / 1000.0
    self.summer     = _cn2["SN"]#us.cn2["SN"]
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
    self.vlm0 = float(_cn2["VM"]) # wert
    self.rlm0 = float(_cn2["RM"]) # wert
    self.vle0 = float(_cn2["VE"]) # wird in anzeige verwendet
    self.rle0 = float(_cn2["RE"])
    self.rls0 = float(_cn2["RS"])
    self.ven0 = float(_cn2["PM"])/10.0
    self.err0 = int  (_cn4["ER"])
    self.fix0 = float(_cn4["FX"])
    self.tmo0 = float(_cn4["MT"])
    self.tan0 = int  (_cn4["NL"])
    return 0, "no error"


  def scan_all(self):
    for modIdx1 in self.modules: # plpl for modIdx in range(20):
      _modIdx = modIdx1 - 1
      _modAdr = modIdx1
      self.box[_modIdx].setFill('orange')                # mark box as active
      answer,y = self.monitor_ping_queue(_modAdr)
      if answer != True :
        self.__set_no_echo_box(_modIdx)
        self.dbg.m("monitor_ping_queue error:",y,cdb=1)
      else: # no echo
        self.__display_header_box(y, _modIdx, _modAdr)
        for controller in [1,2,3] : # fetch status information and display it
          conIdx = controller-1
          _conAbsIdx = self.conAbsIdx = _modIdx*4*4 + conIdx
          e,y = self.status( _modAdr, controller )
          self.dbg.m("_conAbsIdx",_conAbsIdx,"mod:",_modAdr,"controller:",controller,";e:",str(e),";y:",y,cdb=3)
          if e > 0 : # error
              self.dbg.m("e[0]>0:",e,"//y:",y,cdb=1)
              self.__set_error_boxes(_conAbsIdx) #self.__set_rows(_modAdr,_modIdx, (str(_modAdr),str(controller),'e:',e),-1,4)
              self.summer = 0   # make new green error color #_conAbsIdx, _id[2]%(_swap_val_one),#(se
              self.rlm0   = "A" # err val1
              self.rls0   = "B" # err val2
              self.ven0   = "C" # err val3
              self.__set_cn_boxes(_conAbsIdx,_modAdr)
          else:
              self.__set_cn_boxes(_conAbsIdx,_modAdr)

          if self.__end_check(): return True
      self.__set_rows(_modAdr,_modIdx) # location of the 4 extra boxes
    return self.__end_check()

  def __set_cn_boxes(self,_conAbsIdx,_modAdr):
    using_color = []
    _vals = self.__prepare_vars(_conAbsIdx, _modAdr)
    #initialize correct color based on rx value from nano
    using_color = self.__append_colors(using_color,_vals)
    #second selective check an mark a single error field, not the entire line! maybe more visibility?
    self.dbg.m("pre_check_using_color:",using_color,cdb=9)
    if((self.vle0 == 0 or self.vle0 == -127) or (self.rls0==0.0 or self.rls0 == -127) or (self.rlm0==0.0 or self.rlm0==-127)) :
      using_color = self.__set_colors(using_color)
    self.fill_rects   (0,4,using_color, _conAbsIdx) # fill all rects in this run using the using_color - assuming no number is wrong.
    self.box_set_texts(0,4,_vals,       _conAbsIdx)


  def __prepare_vars(self, _conAbsIdx, _modAdr):
    #_flIdx         = _conAbsIdx + feld * 4 #self.flIdx = self.conAbsIdx + feld*4
    _id            =(   0,           0,              '%5.1f',   '%5.1f',  '%5.1f','%3.0f%%')
    _swap_val_one  = self.vle0 if (_modAdr != self.vm_send_mod) else self.vlm0
    #_vals         = (self.summer, self.conAbsIdx, _id[2]%(_swap_val_one),#(self.vlm0),
    _vals          = (self.summer, _conAbsIdx, _id[2]%(_swap_val_one),#(self.vlm0),
                                          _id[3]%(self.rlm0),
                                          _id[4]%(self.rls0),
                                          _id[5]%(self.ven0))
    return _vals

  def __set_error_boxes(self, _conAbsIdx):
    for feld in range(4):
      _flIdx = self.flIdx = _conAbsIdx + feld*4  #self.flIdx = self.conAbsIdx + feld*4
      self.flRec[_flIdx].setFill(self.color_noEcho)
      self.flVal[_flIdx].setText('      ')

  def __display_header_box(self, answer, _modIdx, _modAdr ):
    ping_tries = answer if answer != 'e' else -1                      # ping echo received
    self.box[_modIdx].setFill(self.color_echo)   # light green
    self.get_parameter( _modAdr, 1 )             # get version information; read from parameters of controller 1 read global modFwVersion
    answer,e = self.monitor_get_jumpers_queue(_modAdr)
    if answer == False:
      answer = "err"
      self.dbg.m("monitor_get_jumpers_queue:",answer,"e:",e,cdb=1)
    self.modFwVersion = st.jumpers if answer != "err" else -2 #set jumper if possible - otherwise set to err
    #self.boxTxt[_modIdx].setText("Adr.:%s, V.%sX P(%s)"% (str(_modIdx+1),str(self.modFwVersion),str(ping_tries+1)) )
    if len(str(ping_tries)) > 2: ping_tries = 1
    self.boxTxt[_modIdx].setText("Adr.:%s, V.%02xX P(%s)"% (str(_modIdx+1),self.modFwVersion,str(int(ping_tries)+1)) )

  def __set_rows(self, _modAdr, _modIdx, t=('VM,VE','RM','RS','PM'), p=-1, i=4):
      if _modAdr == 30: self.box_set_text( 1, t[0].split(',')[0], of = (_modIdx*4*4 + p))
      else:             self.box_set_text( 1, t[0].split(',')[1], of = (_modIdx*4*4 + p))
      for x in range(1,4):
        self.box_set_text( 1, t[x], of = (_modIdx*4*4 +  (p+x*i)))

  def __set_no_echo_box(self,_modIdx):
    self.box[_modIdx].setFill(self.color_noEcho)
    self.boxTxt[_modIdx].setText("Adr.:%s         "%(str(_modIdx+1)))
    for controller in [1,2,3] :
      conIdx = controller-1
      conAbsIdx = _modIdx*4*4 + conIdx

      self.summer = 0 # make new green error color #_conAbsIdx, _id[2]%(_swap_val_one),#(se
      self.vle0   = self.vlm0 = controller
      self.rls0   = _modIdx# err val2
      self.ven0   = conIdx# err val3

      for feld in range(4):
        _flIdx = conAbsIdx + feld*4
        # no valid data received - set all grey and blank
        self.flRec[_flIdx].setFill(self.color_noEcho)
        self.flVal[_flIdx].setText('      ')


        self.rlm0   = _flIdx# err val1
      self.__set_cn_boxes(conAbsIdx,_modIdx)

  def __append_colors(self,using_color, _vals):
    _c = str(_vals[0]).lower()
    for i in range(0,4): #  4 set color per line
      if (_c == "s"):
        _uc = self.color_summer
      elif (_c == "w"):
        _uc = self.color_winter
      elif (_c == "0"):
        _uc = self.color_zero
      else:
        _uc = self.color_error
        self.dbg.m("scan_all: ELSE occured should not have happend:",_c,cdb=1)
      using_color.append(_uc)
      self.dbg.m("using_color.append(%s)"%(_uc),cdb=9)
    return using_color

  def __set_colors(self,using_color):
    using_color[0] = self.color_error if (self.vle0 == 0.0 or self.vle0 == -127) else using_color[0]
    using_color[1] = self.color_error if (self.rlm0 == 0.0 or self.rlm0 == -127) else using_color[1]
    using_color[2] = self.color_error if (self.rls0 == 0.0 or self.rls0 == -127) else using_color[2]
    result = all(elem == self.color_error for elem in using_color[:-1])
    if result: using_color[3] = self.color_error
    self.dbg.m("result:",result, "using_color:",using_color,cdb=9)
    #self.dbg.m("SEC_CHECK_ERR] self.vlm0:",self.vlm0,";self.rlm0:",self.rlm0,";self.rls0:",self.rls0,";err_rects:",str(err_rects),cdb=3)
    return using_color

  def __end_check(self):
    try:
      self.cp = self.win.checkMouse()    # clickPoint
      self.key= self.win.checkKey()      # key pressed
    except GraphicsError:
      self.ende = True
    if self.cp != None :
      self.dbg.m("clickPoint=",self.cp)
      self.cpx = self.cp.getX()
      self.cpy = self.cp.getY()
      self.epc = self.endButtonCoord
      self.dbg.m("epc=",self.epc)
      if( (self.epc[0] < self.cpx < self.epc[2]) and self.epc[3] < self.cpy < self.epc[1] ) :
        self.ende = True
    if self.key != "" : # Taste beendet den Screen
      self.ende = True
    return self.ende

  def box_set_texts(self, f:int, t:int, tu:tuple, of= 0 ):
    x = self.conAbsIdx if of == 0 else of
    # store:    0            1              2           3          4          5
    # vals = (self.summer, self.conAbsIdx, self.vlm0, self.rlm0, self.rls0, self.ven0 )
    if len(tu) < 6: # needs to be 6!
      self.dbg.m("set_text error: len(t) < 5:",str(t),cdb=1)
      return 1
    for i in range(f, t):
      self.box_set_text(i,tu[i+2],x)
      self.dbg.m("i:",i,"tu[i+2]:",tu[i+2],"x:",x,cdb=3)
    return

  def box_set_text(self, feld, text, of = 0):
    x = self.conAbsIdx if of == 0 else of
    try:
      return self.flVal[x+feld*4].setText( text )
    except Exception as e:
      self.dbg.m("box_set_text Exception:",e,cdb=-7)

  def fill_rects(self, f, t, col:tuple or list, of = 0):
    x = self.conAbsIdx if of == 0 else of
    i = 0
    for i in range(f,t):
      self.fill_rect(i, col[i], x )
      i += 1

  def fill_rect(self, id, col, of = 0 ):
    x = self.conAbsIdx if of == 0 else of
    try:
      return self.flRec[x+id*4].setFill(col)
    except Exception as e:
      self.dbg.m("fill_rect Exception:",e,cdb=-7)
mon_obj = MonitorDirect()

if __name__ == "__main__":
  mon_obj = MonitorDirect()
  us.ser_obj.ser_check()
  mon_obj.runme()
  pass

