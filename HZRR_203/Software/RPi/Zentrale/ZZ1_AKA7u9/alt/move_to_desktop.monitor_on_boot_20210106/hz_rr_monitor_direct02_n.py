

"""
Created on Sun Nov 27 21:07:11 2016

@author: pi
"""
from calendar import c
import copy
import threading as th
import time
import numpy as np
import re

#import modbus_b  as mb
#import rr_parse as parse
import hr2_variables as hrv
import hz_rr_config as cg
import hz_rr_debug as dbeg
import usb_ser_b as us
from graphics import *
from hr2_variables import *

def add_mon_queue(ser_bus_work:tuple):
  _temp = list(ser_bus_work)
  _temp.append(mon_obj.ret_mon_q)
  _new_work   = tuple(_temp)
  _work, retv = us.ser_add_work(_new_work,mon_r=True)

  #x = "((0, 'h6742SER_ADD_WORK_RNDY7FZbTZQqtK4249'),)"
  #_pa = re.compile('["|(|)]')
  ##retv = _pa.subn('',retv)

  mon_obj.dbg.m("_work:",_work,cdb=2)
  mon_obj.dbg.m("retv:",tuple(retv),cdb=2)
  _r = ""
  if _work == False: # give back default variables
    return False,retv[1]
  try:
    #test = tuple(map(str, retv[1].replace('(','').replace(')','').split[',']))
    #print("test:",test[0])
    _r = retv[1].replace('(','').replace(')','').replace("'",'')[:-1].split(", ")
    _r = _r[-1] if (type(_r) == str or type(_r) == list) else int(_r)
  except Exception as e:
    mon_obj.dbg.m("add_mon_queue exception:",e,cdb=3)

  mon_obj.dbg.m('add_mon_queue:',ser_bus_work[0],":",_r,cdb=3)
  return retv[0], _r

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
    self.jobs             = []
    self.mon_updates      = []
    self.val              = np.ones((30,4,4))       # values to be diaplayed
    self.val              = self.val*(-99.9)        # stands for 'no vlaue'
    self.pval             = np.zeros((30,4,4,2))    # text coordinates x/y for values
    self.summer           = {}#"X"  mod:{reg:val}
    self.vlm0             = {}#-99.9
    self.rlm0             = {}#-99.9
    self.vle0             = {}#-99.9
    self.rle0             = {}#-99.9
    self.rls0             = {}#-99.9
    self.ven0             = {}#-99.9
    self.err0             = {}#  0
    self.fix0             = {}#-99.9
    self.tmo0             = {}#-99.9
    self.tan0             = {}#  0
    self.vm_send_mod      = self.modTVor
    self.modFwVersion     = ""
    self.ret_mon_q        = "ret_mon_q"
    self.win              = ""#GraphWin()
    self.monitor_start    = 0
    self._init_vars()
    #self.special_box_id   = 29
  # get hostname of computer
  def get_hostname(self):
      f = open("/etc/hostname","r")
      zzName = f.readline().strip()
      f.close()
      return zzName


  def _init_vars(self):
    h = cg.hkr_obj.get_heizkreis_config()
    if len(h) > 5:
        (self.heizkreis, self.modules, self.modTVor, self.modSendTvor, self.dtLog, self.filtFakt) = h
    else:
        (self.heizkreis, self.modules, self.modTVor, self.modSendT, self.dtLog ,self.filtFakt) =  (0,[],0,[],180,0.1)
    self.vm_send_mod = self.modTVor

    vars = (self.summer,self.vlm0,self.rlm0,self.vle0,self.rle0,self.rls0,self.ven0,self.err0,self.fix0,self.tmo0,self.tan0)
    varse = {"self.summer":'',"self.vlm0":'',"self.rlm0":'',"self.vle0":'',"self.rle0":'',"self.rls0":'',"self.ven0":'',"self.err0":'',"self.fix0":'',"self.tmo0":'',"self.tan0":''}
    vals =  ("",-99.9,-99.9,-99.9,-99.9,-99.9,-99.9,0,-99.9,-99.9,0)
    c = 0
    for _s in varse.keys():
      varse[_s] = vals[c]
      c +=1
    #print(varse)
    for _va in varse.keys():
      _e = f"{_va} = dict()"
      exec(_e)
      #print("_exec:",_e)

      for _m in self.modules:
        _e = f"{_va}['{_m}'] = dict()"
        exec(_e)
        #print("_exec:",_e)

        for _r in [1,2,3]:
          _e = f"{_va}['{_m}']['{_r}'] = dict()"
          exec(_e)
          #print("_exec:",_e)

          _mod = str(_m)
          _reg = str(_r)
          _e = f"{_va}['{_mod}']['{_reg}'] = '{varse[_va]}'" if type(varse[_va]) == str else f"{_va}['{_mod}']['{_reg}'] =  float('{varse[_va]}')"
          exec(_e)
          #print("_exec:",_e)

    print("self.summer:",self.summer)

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

      self._w_joblist()
      self._w_startall()

      while not self.ende:
        time.sleep(0.01)
        loop += 1
        self.ende = self.scan_all()

      self.dbg.m("loop run:",loop,cdb=3)
      self._w_stopall()
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
    self._reset_status(modAdr, subAdr)
    return add_mon_queue( ser_bus_work=("read_stat",modAdr,subAdr) )
    #_work         = us.ser_add_work(("read_stat",modAdr,subAdr,self.ret_mon_q))
    #if _work[0] == False: # give back default variables
    #  return False,_work[1]
    #self.dbg.m("monitor_read_stat_queue assigning:",hrv.get_cn('m')[0],"//",hrv.get_cn('m')[1],cdb=3)
    #return True,_work[1]

  def monitor_ping_queue(self,modAdr):
    return add_mon_queue( ser_bus_work=("ping",modAdr) )
    #_work         = us.ser_add_work(("ping",modAdr,self.ret_mon_q))
    #if _work[0] == False: # give back default variables
    #  return False,_work[1]
    #self.dbg.m("monitor_ping_queue:",_work[1],cdb=3)
    #return True, us.ser_obj.tries_last_ping

  def get_parameter(self, modAdr, controller ) :
    return add_mon_queue( ser_bus_work=("get_param",modAdr,controller) )
    #_work         = us.ser_add_work(("get_param",modAdr,controller,self.ret_mon_q))
    #if _work[0] == False: # give back default variables
    #  return False,_work[1]
    #self.dbg.m("get_parameter:",_work[1],cdb=3)
    #return True, _work[1]

  def monitor_get_jumpers_queue(self, modAdr):
    return add_mon_queue( ser_bus_work=("get_jumpers",modAdr) )
    #_work         = us.ser_add_work()
    #if _work[0] == False: # give back default variables
    #  return False,_work[1]
    #self.dbg.m("monitor_get_jumpers_queue:",_work[1],cdb=3)
    #return True, _work[1]


  def _reset_status(self,mod,reg):
    self.dbg.m("_reset_status: resetting monitor vars",cdb=3)
    self.zDateSec   = 0
    self.hkr        = 0
    self.modnr      = 0
    self.command    = 0
    self.control    = 0
    self.protVer    = ""
    self.modTStamp  = 0
    _mod,_reg       = str(mod),str(reg)
    #self.summer     = {key:"" for key in self.summer}
    #self.vlm0       = {key: 0 for key in self.vlm0[_mod][_reg]}
    #self.rlm0       = {key: 0 for key in self.rlm0[_mod][_reg]}
    #self.vle0       = {key: 0 for key in self.vle0[_mod][_reg]}
    #self.rle0       = {key: 0 for key in self.rle0[_mod][_reg]}
    #self.rls0       = {key: 0 for key in self.rls0[_mod][_reg]}
    #self.ven0       = {key: 0 for key in self.ven0[_mod][_reg]}
    #self.err0       = {key: 0 for key in self.err0[_mod][_reg]}
    #self.fix0       = {key: 0 for key in self.fix0[_mod][_reg]}
    #self.tmo0       = {key: 0 for key in self.tmo0[_mod][_reg]}
    #self.tan0       = {key: 0 for key in self.tan0[_mod][_reg]}
    hrv.reset_cn('m')

  def status(self, modAdr, controller ):
    # get status information from module modAdr and
    # controller; 0 = module status information
    _mod,_reg = str(modAdr),str(controller)
    x,y = "", ""
    try:
      x,y = self.monitor_read_stat_queue(int(modAdr),(controller))
      self.dbg.m("status(",modAdr,",",controller,") = "+ str(x))
    except Exception as e:
      self.dbg.m("read_stat error:", e,"//y:",y, cdb=-7)
      return 1, "read_stat error -> x:"+x+" //y: " +y
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
    self.summer[_mod][_reg]    = _cn2["SN"]#us.cn2["SN"]
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
    self.vlm0[_mod][_reg] = float(_cn2["VM"]) # wert
    self.rlm0[_mod][_reg] = float(_cn2["RM"]) # wert
    self.vle0[_mod][_reg] = float(_cn2["VE"]) # wird in anzeige verwendet
    self.rle0[_mod][_reg] = float(_cn2["RE"])
    self.rls0[_mod][_reg] = float(_cn2["RS"])
    self.ven0[_mod][_reg] = float(_cn2["PM"])/10.0
    self.err0[_mod][_reg] = int  (_cn4["ER"])
    self.fix0[_mod][_reg] = float(_cn4["FX"])
    self.tmo0[_mod][_reg] = float(_cn4["MT"])
    self.tan0[_mod][_reg] = int  (_cn4["NL"])
    return 0, "no error"

  def _w_startall(self):
    for slaves in self.jobs:
      slaves.start()

  def _w_stopall(self):
    for slaves in self.jobs:
      try:
        slaves.stop()
      except:
        pass
    self._w_joblist()

  def w_watcher(self):
    _ttl = time.time() + 300
    while True:
      for slaves in self.jobs:
        _iI = isinstance(slaves,th.Thread)
        if _iI:
          if not slaves.is_alive():
            self.dbg.m("w_watcher -> restarting '",slaves,"'",cdb=-7)
            try:
              slaves.start()
            except Exception as e:
              self.dbg.m("w_watcher -> restart of'",slaves,"' failed",cdb=-7)
      time.sleep(1)
      self.dbg.m("w_watcher -> sleeping, no. of jobs:'",len(self.jobs),cdb=3)

  def _w_manager(self):
    pass

  def _w_joblist(self):
    _jl = []
    for x in self.modules:
      _modIdx, _modAdr = x-1, x
      _t = th.Thread(target=self.w_box_header,args=(_modAdr,_modIdx))
      _t.setDaemon(True)
      print("_t:",_t)
      _jl.append(_t)
      for r in [1,2,3]: # regler bots
        _r = th.Thread(target=self.w_box_content,args=(_modAdr,r,_modIdx))
        _r.setDaemon(True)
        print("_r:",_r)
        _jl.append(_r)
    _e = th.Thread(target=self.w_watcher)
    _e.setDaemon(True)
    print("_jl:",_jl)
    _jl.append(_e)
    self.dbg.m("_w_joblist:",_jl,cdb=1)
    self.jobs = _jl
    return self.jobs

  def _w_monitor_send_update(self,call):
    self.__w_monitor_add_to_list(call)

  def _w_monitor_draw_updates(self):
    _updates = self._w_monitor_update_list()
    if len(_updates) > 0:
      try:
        _up = _updates.pop(0)
        self.dbg.m('executing:',_up,cdb=-7)
        self.__w_monitor_exec(_up)
      except Exception as e:
        self.dbg.m("_w_monitor_draw_updates Exception:",e,cdb=-7)
    else:
      ti.sleep(0.01)

  def _w_monitor_update_list(self):
    return self.mon_updates

  def __w_monitor_add_to_list(self,call):
    self.mon_updates.append(call)
    _ttl = time.time () + 300
    while self.__w_monitor_request_completed(call):
      if (time.time() > _ttl): break
      self.dbg.m('__w_monitor_add_to_list: sleeping..(%s)'%(str(int(_ttl)-int(time.time()))))
      time.sleep(1)

  def __w_monitor_request_completed(self,c):
    try:
      self.mon_updates.index(c)
      self.dbg.m("__w_monitor_request_completed:",not (self.mon_updates.index(c)),cdb=3)
    except Exception as e:
      return True
    return False

  def __w_monitor_exec(self,cmd):
    _r = ""
    _locals = locals()
    self.dbg.m("__w_monitor_exec:",cmd,cdb=3)
    try:
        #exec(_exec, globals(), _locals )
        #exec(_exec, None, {'self': self} )
        #exec(_exec, locals(), locals())
        exec(cmd, globals(), locals())
    except Exception as e:
        self.dbg.m("watch your formatting(%s)//"%(cmd),e,cdb=-7)
        return False
    return _locals['_r']

  # job for worker
  def w_box_header(self,_modAdr,_modIdx):
    while self.monitor_start:
      try:
        answer,y = self.monitor_ping_queue(_modAdr)
        if answer != True :
          self._w_monitor_send_update(f'self.set_no_echo_box({_modIdx})')
          self.dbg.m("monitor_ping_queue error:",y,cdb=1)
        else: # no echo
          self._w_monitor_send_update(f'self.display_header_box(3, {_modIdx}, {_modAdr})')

        self._w_monitor_send_update(f'self.set_rows({_modAdr},{_modIdx})')
      except Exception as e:
        self.dbg.m(f"w_box_header Exception(mod={_modAdr})(idx={_modIdx}):",e,cdb=-7)

  def w_box_content(self, _modAdr, controller, _modIdx):
    _ma,_ca = str(_modAdr),str(controller)
    while self.monitor_start:
      try:
        conIdx = controller-1
        _conAbsIdx = self.conAbsIdx = _modIdx*4*4 + conIdx
        _cai = _conAbsIdx
        e,y = self.status( _modAdr, controller )
        self.dbg.m("_conAbsIdx",_conAbsIdx,"mod:",_ma,"controller:",_ca,";e:",str(e),";y:",y,cdb=3)
        if e > 0 : # error
            self.dbg.m("e[0]>0:",e,"//y:",y,cdb=1)
            self._w_monitor_send_update(f'self.set_error_boxes({_cai})') #self._set_rows(_modAdr,_modIdx, (str(_modAdr),str(controller),'e:',e),-1,4)
            self.summer[_ma] = 0   # make new green error color #_conAbsIdx, _id[2]%(_swap_val_one),#(se
            self.rlm0[_ma][_ca]   = "0" # err val1
            self.rls0[_ma][_ca]   = "1" # err val2
            self.ven0[_ma][_ca]   = "2" # err val3
            self._w_monitor_send_update(f'self.set_cn_boxes({_cai},{int(_ma)},{int(_ca)})')
        else:
            self._w_monitor_send_update(f'self.set_cn_boxes({_cai},{int(_ma)},{int(_ca)})')

      except Exception as e:
        self.dbg.m("w_box_header Exception:",e,cdb=-7)


  def scan_all(self):
    self._w_monitor_draw_updates()
    self.set_rows(4,3)
    return self.__end_check()


  def __prepare_vars(self, _conAbsIdx, _modAdr, _r):
    #_flIdx         = _conAbsIdx + feld * 4 #self.flIdx = self.conAbsIdx + feld*4
    _id            =(   0,           0,              '%5.1f',   '%5.1f',  '%5.1f','%3.0f%%')
    _swap_val_one  = self.vle0[str(_modAdr)][str(_r)] if (_modAdr != self.vm_send_mod) else self.vlm0[str(_modAdr)][str(_r)]
    #_vals         = (self.summer, self.conAbsIdx, _id[2]%(_swap_val_one),#(self.vlm0),
    _vals          = (self.summer[str(_modAdr)][str(_r)],
                  _conAbsIdx, _id[2]%(_swap_val_one),
                              _id[3]%(self.rlm0[str(_modAdr)][str(_r)]),
                              _id[4]%(self.rls0[str(_modAdr)][str(_r)]),
                              _id[5]%(self.ven0[str(_modAdr)][str(_r)]))
    return _vals

  def set_error_boxes(self, _conAbsIdx):
    for feld in range(4):
      _flIdx = self.flIdx = _conAbsIdx + feld*4  #self.flIdx = self.conAbsIdx + feld*4
      self.flRec[_flIdx].setFill(self.color_noEcho)
      self.flVal[_flIdx].setText('      ')

  def display_header_box(self, answer, _modIdx, _modAdr ):
    ping_tries = answer if answer != 'e' else -1                      # ping echo received
    self.__w_monitor_add_to_list(f'self.box[{_modIdx}].setFill("{self.color_echo}")')   # light green
    self.get_parameter( _modAdr, 1 )             # get version information; read from parameters of controller 1 read global modFwVersion
    answer,e = self.monitor_get_jumpers_queue(_modAdr)
    if answer == False:
      answer = "err"
      self.dbg.m("monitor_get_jumpers_qureue:",answer,"e:",e,cdb=1)
    self.modFwVersion = st.jumpers if answer != "err" else -2 #set jumper if possible - otherwise set to err
    #self.boxTxt[_modIdx].setText("Adr.:%s, V.%sX P(%s)"% (str(_modIdx+1),str(self.modFwVersion),str(ping_tries+1)) )
    if len(str(ping_tries)) > 2: ping_tries = 1
    #self.boxTxt[_modIdx].setText("Adr.:%s, V.%02xX P(%s)"% (str(_modIdx+1),self.modFwVersion,str(int(ping_tries)+1)) )
    _hs = f'self.boxTxt[{_modIdx}].setText("Adr.:%s, V.%02xX P(%s)"% (str({_modIdx}+1),{self.modFwVersion},str(int({ping_tries})+1)) )'
    self.__w_monitor_add_to_list(_hs)

  def set_rows(self, _modAdr, _modIdx, t=('VM,VE','RM','RS','PM'), p=-1, i=4):
      if _modAdr == 30: self.box_set_text( 1, t[0].split(',')[0], of = (_modIdx*4*4 + p))
      else:             self.box_set_text( 1, t[0].split(',')[1], of = (_modIdx*4*4 + p))
      for x in range(1,4):
        self.box_set_text( 1, t[x], of = (_modIdx*4*4 +  (p+x*i)))

  def set_no_echo_box(self,_modIdx):
    self.box[_modIdx].setFill(self.color_noEcho)
    self.boxTxt[_modIdx].setText("Adr.:%s         "%(str(_modIdx+1)))
    for controller in [1,2,3] :
      conIdx = controller-1
      conAbsIdx = _modIdx*4*4 + conIdx

      self.summer[str(_modIdx+1)][str(controller)] = 0 # make new green error color #_conAbsIdx, _id[2]%(_swap_val_one),#(se
      self.vle0[str(_modIdx+1)][str(controller)]   = self.vlm0 = controller
      self.rls0[str(_modIdx+1)][str(controller)]   = _modIdx# err val2
      self.ven0[str(_modIdx+1)][str(controller)]   = conIdx# err val3

      for feld in range(4):
        _flIdx = conAbsIdx + feld*4
        # no valid data received - set all grey and blank
        self.flRec[_flIdx].setFill(self.color_noEcho)
        self.flVal[_flIdx].setText('      ')
        self.rlm0[str(_modIdx+1)][str(controller)]  = _flIdx# err val1
      self.set_cn_boxes(conAbsIdx,_modIdx,controller)

  def set_cn_boxes(self,_conAbsIdx,_modAdr, _r):
    try:
      using_color = []
      _vals = self.__prepare_vars(_conAbsIdx, _modAdr, _r)
      #initialize correct color based on rx value from nano
      using_color = self.__append_colors(using_color,_vals)
      #second selective check an mark a single error field, not the entire line! maybe more visibility?
      self.dbg.m("pre_check_using_color:",using_color,cdb=9)
      if((self.vle0[str(_modAdr)][str(_r)] == 0 or self.vle0[str(_modAdr)][str(_r)] == -127) or
      (self.rls0[str(_modAdr)][str(_r)]==0.0 or
      self.rls0[str(_modAdr)][str(_r)] == -127) or
      (self.rlm0[str(_modAdr)][str(_r)]==0.0 or
      self.rlm0[str(_modAdr)][str(_r)]==-127)) :
        using_color = self.__set_colors(using_color,_modAdr,_r)
      self.__w_monitor_add_to_list(f'self.fill_rects(0,4,{using_color},{_conAbsIdx})') # fill all rects in this run using the using_color - assuming no number is wrong.
      self.__w_monitor_add_to_list(f'self.box_set_texts(0,4,{_vals},   {_conAbsIdx})')
    except Exception as e:
      self.dbg.m("set_cn_boxes Exception:",e,cdb=-7)

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

  def __set_colors(self,using_color,mod,reg):
    _m, _r = str(mod),str(reg)
    using_color[0] = self.color_error if (self.vle0[_m][_r] == 0.0 or self.vle0[_m][_r] == -127) else using_color[0]
    using_color[1] = self.color_error if (self.rlm0[_m][_r] == 0.0 or self.rlm0[_m][_r] == -127) else using_color[1]
    using_color[2] = self.color_error if (self.rls0[_m][_r] == 0.0 or self.rls0[_m][_r] == -127) else using_color[2]
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

