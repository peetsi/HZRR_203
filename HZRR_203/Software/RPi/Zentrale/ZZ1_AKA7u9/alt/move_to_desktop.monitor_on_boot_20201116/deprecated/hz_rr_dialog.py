#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
HZ-RR012 RS485 dialog

Created on Sat Nov 19 10:35:52 2016

@author: Peter Loster (pl)

"""
import sys
import time
import numpy       as np
import usb_ser     as us
import modbus      as mb
import param_11c   as par_c
import param_11d   as par_d
import heizkreis_config as hkr_cfg

#import RPi.GPIO   as GPIO


# *** global variables
par = par_d
err = 0
err |= us.serial_connect()
err |= us.ser_open()
print("Fehler=%d"%(err))

# *** voreingestellte Werte modAdr = 1
reg    = 0
intSec = 10           # intervall zum Abruf der Statusanzeige
modAdr = 1
wdh    = 300/intSec   # wiederhole 5 Minuten lang die anzeige
vers = ['HZ-RR11c', 'HZ-RR11d']
versTxt= ['(vom 12.12.2016)', '(vom 19.12.2016)']
modFwVersion = vers[1]


def read_heizkreis_config() :
    global heizkreis, modules, modTVor, modSendTvor, dtLog, filtFakt
    
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



def menu(x):
  # x=0: zeige Menü für Auswahl
  print('Modul Adresse = %d; Firmware Version=%s'%(modAdr,modFwVersion))
  print(' 0   Ende')
  print(' A   Modul Adresse                   V   Modul Firmware Version')
  print(' 1   Teste Modul-Adresse (ping)')
  print(' 2   Staus: anzeigen;                3   alle %dsec anzeigen'%intSec)
  print(' 4   Parameter lesen                 5   alle Param.-> Werkseinst.')
  print(' 6   Ventil dauerhaft auf            7   Ventil dauerhaft zu')
  print(' 8   Ventil regeln (Ende dauerhaft)')
  print(' 9   Regler inaktiv setzen          10   Regler aktiv setzen')
  print('11   schneller Ablauf fuer Test     12   normale Geschwindigkeit')
  print('20   sende Vorlauftemperatur von Zentrale')
  print('21   neue Parameter senden          31   alle Parameter ins EEPROM')
  print('40   Parameter aller Module abholen und in Datei speichern')
  print(60*"-")
  print('Vorsicht: 49   Reset ueber Watchdog')
  print('Vorsicht: 50   jede Minute status abspeichern'  )
  print('')
  a = input('Wahl? ')
  if a=='a' or a=='A' :
    return 99
  if a=='v' or a=='V' :
    return 98
  return int(a)


def select_controller():
  fertig = False
  while not fertig :
    a = input( 'module=0; regler=1,2,3,4; alle=5; Ende=9; wahl? ')
    try:
      reg = int(a)
      if reg == 5 :
        return[1,2,3,4]
      elif reg <= 4 :
        return [reg]
      elif reg == 9 :
        return []
    except:
      pass


def perform_command( controllers, command ) :
  for reg in controllers:
    cmd = mb.wrap_modbus( modAdr, command, reg, "" )
    print('sende:  %s'%(cmd))
    rxCmd = us.txrx_command( cmd )
    print('empfange: %s'%( rxCmd ) )


def select_version() :
  global par
  global vers
  global versTxt
  i=0
  for ver in range( len(vers) ) :
    print('%d   %s  %s'%(i+1,vers[i],versTxt[i]))
    i += 1
  wahl=0
  while not wahl :
    a = input("Wahl ?")
    try:
      wahl = int(a)
    except:
      wahl = 0
      pass
    if wahl < 0         :  wahl = 0
    if wahl > len(vers) :  wahl = 0 
  print('wahl=%d, version %s'%(wahl, vers[wahl-1]))
  if wahl == 1:
    par = par_c
  if wahl == 2:
    par = par_d
  return vers[wahl-1]




def doit( wahl ):
  global modAdr
  global index
  global par
  global modFwVersion

  if wahl == 1 :  # Teste Modul-Adresse (ping)
    err = us.ser_reset_buffer()
    txCmd = mb.wrap_modbus( modAdr, 1, 0, "" )
    print(txCmd)
    rxCmd = us.txrx_command( txCmd )
    print('empfange: %s'%( rxCmd ) )

  if wahl == 2 :  # Staus: anzeigen;
    err = us.ser_reset_buffer()
    controllers = select_controller()
    perform_command( controllers, 0x02 )

  if wahl == 3 :  # alle %dsec anzeigen
    w = wdh
    while( w ) :
      for reg in [1,2,3,4]:
        txCmd = mb.wrap_modbus( modAdr, 2, reg, "" )
        print('sende:  %s'%(txCmd))
        rxCmd = us.txrx_command( txCmd )
        print('empfange: %s'%( rxCmd ) )
      time.sleep(intSec)
      w -= 1
      print()

  if wahl == 4 :  # Parameter lesen 
    tbl=[]
    for regler in [0,1,2,3,4]:
      txCmd = mb.wrap_modbus( modAdr, 3, regler, "" )
      print('sende:  %s'%(txCmd))
      rxCmd = us.txrx_command( txCmd )
      cmdList = rxCmd
      print(rxCmd)
      tbl1 = cmdList.split()
      tbl.append( tbl1 )
      #print('empfange: %s'%( rxCmd ) )
    # sort as a table:
    spalten = len(tbl)
    zeilen  = len(tbl[0])
    print(zeilen,spalten)
    for x in range(zeilen):
      zs=[]
      for y in range(spalten):
        zs.append(tbl[y][x])

      print("%10s  %5s %5s %5s %5s"%(zs[0],zs[1],zs[2],zs[3],zs[4]))

  if wahl == 5 :  # alle Parameter auf Werkseinstellung setzen
    perform_command( [0], 0x30 )

  if wahl == 6 :  # Ventil dauerhaft auf
    controllers = select_controller()
    perform_command( controllers, 0x31 )

  if wahl == 7 :  # Ventil dauerhaft zu
    controllers = select_controller()
    perform_command( controllers, 0x32 )

  if wahl == 8 :  # Ventil regeln (Ende dauerhaft)
    controllers = select_controller()
    perform_command( controllers, 0x33 )

  if wahl == 9 :  # Regler inaktiv setzen 
    controllers = select_controller()
    perform_command( controllers, 0x34 )

  if wahl == 10 :  # controller active
    controllers = select_controller()
    perform_command( controllers, 0x35 )

  if wahl == 11 :  # fast
    controllers = select_controller()
    perform_command( controllers, 0x36 )


  if wahl == 12 :  # end fast -> normal speed
    controllers = select_controller()
    perform_command( controllers, 0x37 )

  if wahl == 20 :  # sende Vorlauftemperatur von Zentrale
    vtzstr = input("Zentrale Vorlauftemperatur:")
    cmd = mb.wrap_modbus( modAdr, 0x20, 0, ' '+vtzstr+' ' )
    print('sende:  %s'%(cmd))
    rxCmd = us.txrx_command( cmd )
    print('empfange: %s'%( rxCmd ) )
    

  if wahl == 21 :  # parameter senden
    controllers = select_controller()
    for reg in controllers:
      cmd=modFwVersion
      for i in par.index:
        cmd += ' ' + par.valFst[i]%( par.valDef[i] )
      cmd += ' '
      txCmd = mb.wrap_modbus( modAdr, 0x21, reg, cmd )
      print( 'sende: %dbyte, cmd=%s'%(len(txCmd), txCmd ))
      rxCmd = us.txrx_command( txCmd )
      print('empfange: %s'%( rxCmd.strip() ) )
      dtEeprom = 0.2
      print('warte %d sec bis Befehl ausgeführt ist ...'%(dtEeprom))
      print("-"*40)
      time.sleep(dtEeprom)

  if wahl == 31 :  # parameter ins eeprom speichern
    reg=0
    cmd = mb.wrap_modbus( modAdr, 0x39, reg, "" )
    print('sende:  %s'%(cmd))
    rxCmd = us.txrx_command( cmd )
    print('empfange: %s'%( rxCmd ) )

  if wahl == 40 :  # parameter aller module abholen und abspeichern
      pass
      dateTime = time.strftime( "%Y%m%d_%H%M%S", time.localtime())
      datName = "log/par_hk%d_%s.dat"%(heizkreis, dateTime)
      print("Schreibe Datei: %s"%(datName))
      fout = open(datName,"w")
      
      print("Modul:",end="")
      for moduleAdr in modules:
          print(moduleAdr," ", end="")
          for regler in [0,1,2,3,4]:
              txCmd = mb.wrap_modbus( moduleAdr, 3, regler, "" )
              #print('sende:  %s'%(txCmd))
              rxCmd = us.txrx_command( txCmd )
              hs = "Mod%d Reg%d %s\r\n"%( moduleAdr, regler, rxCmd )
              fout.write(hs)
      print(" fertig")
      fout.close()

  if wahl == 49:  # reset ueber Watchdog auslösen
    print('Modul Adresse ist %d'%(modAdr))
    cmd = mb.wrap_modbus( modAdr, 0x3A, 0, "" )
    print('sende:  %s'%(cmd))
    rxCmd = us.txrx_command( cmd )
    print('empfange: %s'%( rxCmd ) )


  if wahl == 50:  # jede Minute status einlesen und speichern
    print('Modul Adresse ist %d'%(modAdr))

    dateiName = 'log/log_HZ-RR012_'+time.strftime('%Y-%M-%d_%H:%M:%S.dat')
    odat = open( dateiName, 'w' )
    while True :
      for regler in [1,2,3,4]:
        txCmd = mb.wrap_modbus( modAdr, 2, regler, "" )
        #print('sende:  %s'%(cmd))
        rxCmd = us.txrx_command( txCmd )
        logstr = time.strftime('%Y-%M-%d_%H:%M:%S ') + rxCmd
        print('store: %s'%( logstr ) )
        odat.write( logstr + '\r\n' )
      odat.flush()
      time.sleep(60.0)
      print()

  if wahl == 98 :
    modFwVersion = select_version()

  if wahl == 99 :
    a=0
    while a<1 or a >31 :
      a = int( input( 'Modul Adresse 1..30; wahl? ') )
    modAdr = a
  print()


wahl = 1
while wahl > 0 :
    read_heizkreis_config()
    wahl = menu(0)
    print( "----------------wahl=%d-------------"%(wahl) )
    doit(wahl)
