# -*- coding: utf-8 -*-
"""
Created on Mon Nov 21 22:42:34 2016

@author: pi
"""

from usb_ser import *

import vorlaut as vor


def checksum( s ) :
  cs = 0
  for c in s :
    try:
      cs += ord(c)
    except Exception as e :
      cs = 0          # generate wrong checksum intentionally
      # TODO sotre e in logfile
  cs = cs & 0xFFFF    # make unsigned 16 bit
  return cs


def lrc_parity( s ) :
  # s contains whole string to be wrapped; for
  lrc = 0;
  for c in s :
    # TODO error:"ord() expected string of length 1, but int found"
    #      abfangen
    try:
      lrc = lrc ^ ord(c)
    except Exception as e :
      lrc = 0               # generate wrong lrc inentionally
      # store e in logfile
  lrc = lrc & 0x00FF
  return lrc


def wrap_modbus( adr, fnc, contr, cmdstr ) :
  # adr      module address
  # fnc      function number
  # contr    regulator number 1,2,3,4 or 0 for module
  # cmdstr   command-string; could be "" empty
  cmd = "%02X%02X%1X%s"%(adr, fnc, contr, cmdstr )
  cs = checksum( cmd )
  cmd = "%s%04X"%(cmd,cs)
  lrc = lrc_parity( cmd )
  cmd = ":%s%02X\r\n"%(cmd, lrc)
  cmd = cmd.encode()
  return cmd


def unwrap_modbus( line ) :
  # calculate checksum and parity of received line
  calcLrc = 0
  calcCsm = 0
  lineLrc = 0
  lineCsm = 0

  err_rx = 0
  l = len( line )
  if l==0 :
    err_rx |= 1
    return "err: len=0"

  s0 = line[l-4:l-2]
  s0 = s0.upper()           # user only uppercase hex 'A'...'F'
  try:
    lineLrc = int(s0,base=16)
  except Exception as e:
    vor.vorlaut(3,e)
    err_rx |= 2
  else:
    calcLrc  = lrc_parity( line[ 1 : l-4 ] )

  s1 = line[l-8:l-4]
  s1 = s1.upper()           # user only uppercase hex 'A'...'F'
  try:
    lineCsm = int(s1,base=16)
  except Exception as e:
    vor.vorlaut( 3, e)
    err_rx |= 4
    # fliegt raus -> stoppt Programm
  calcCsm  = checksum( line[ 1 : l-8 ] )

  vor.vorlaut( 3,  "cmd=%s"%(line))
  vor.vorlaut( 3,  "%s lineCs =%04X calcCs =%04X"%(s1,lineCsm,calcCsm))
  vor.vorlaut( 3,  "%s lineLrc=%02X calcLrc=%02X"%(s0,lineLrc,calcLrc))
  if lineLrc==calcLrc and lineCsm==calcCsm :
    return line[ 0 : l-8 ]
  else:
    vor.vorlaut( 3, "error %04X in received string"%(err_rx))
    return "err_rx=%04X"%(err_rx)





