# -*- coding: utf-8 -*-
"""
module ser.pi
RS-485 Interface over USB adapter

Created on Sat Nov 19 10:37:27 2016

@author: pl
"""

import serial

import modbus as rmb
import vorlaut as vor

#serPort = "/dev/ttyUSB0" # USB0 might change
# fixed for the same adapter is always:
#serPort = "/dev/serial/by-id/usb-FTDI_FT232R_USB_UART_A504YCFM-if00-port0"
# has problems if the adapter changes (because of serial number)
# so we use the USB-socket where the adapter is connected:
# Bottom socket next to Ethernet socket:
serPort = "/dev/serial/by-path/platform-3f980000.usb-usb-0:1.3:1.0-port0"
serPort = "/dev/serial/by-path/platform-3f980000.usb-usb-0:1.1.3:1.0-port0" #"/dev/serial/by-path/platform-3f980000.usb-usb-0:1.3:1.0-port0/move_to_desktop.monitor_on_boot/"


def serial_connect() :
  global ser
  err=0
  try:
    ser = serial.Serial(
      port=serPort,
      baudrate =19200,
      parity=serial.PARITY_NONE,
      stopbits=serial.STOPBITS_TWO,
      bytesize = serial.EIGHTBITS,
      timeout = 0.2)
  except serial.SerialException as e:
    vor.vorlaut( 3,  "01 cannot find: %s"%(serPort))
    vor.vorlaut( 3,  "   exception = %s"%(e))
    err = 1
  except Exception as e:
    vor.vorlaut( 3,  "02 something else is wrong with serial port: %s"%(serPort))
    vor.vorlaut( 3,  "   exception = %s"%(e))
    err = 2
  return err



def ser_open():
  # open USB->RS485 connection
  global ser
  err=0
  try:
    ser.open()
  except serial.SerialException as e:
    vor.vorlaut( 3,  "03 cannot open: %s"%(serPort))
    vor.vorlaut( 3,  "   exception = %s"%(e))
    err = 3
  except  Exception as e:
    vor.vorlaut( 3,  "04 something else is wrong with serial port: %s"%(serPort))
    vor.vorlaut( 3,  "   exception = %s"%(e))
    err = 4
  return err


def ser_reset_buffer():
  global ser
  err=0
  try:
    ser.flushOutput()  # newer: ser.reset_output_buffer()
    ser.flushInput()   # newer: ser.reset_input_buffer()
  except serial.SerialException:
    err = 5
    vor.vorlaut( 3,  "05 cannot erase serial buffers")
    vor.vorlaut( 3,  "   exception = %s"%(e))
  except Exception as e:
    err = 6
    vor.vorlaut( 3,  "06 something else is wrong with serial port: %s"%(serPort))
    vor.vorlaut( 3,  "   exception = %s"%(e))
  return err


def txrx_command( txCmd ) :

  global ser
  global line
  twait1 = 0.01
  twait2 = 0.01

  ser.flushInput()
  ser.flushOutput()
  vor.vorlaut( 2, "\ntx: %s"%(txCmd[:-2]))
  try:
    ser.write(txCmd)                  # start writing string
  except serial.SerialTimeoutException as e:
    vor.vorlaut( 2, "07 timeout sending string: %s"%(cmd))
    vor.vorlaut( 2,  "  exception = %s"%(e))
  except serial.SerialException:
    vor.vorlaut( 2,  "08 SerialException on write")
    vor.vorlaut( 2,  "   exception = %s"%(e))
    ser.close()
  except   Exception as e:
    vor.vorlaut( 2,  "09 error serial port %s, writing"%(serPort))
    vor.vorlaut( 2,  "   exception = %s"%(e))
    ser.close()

  ser.flush()

  #time.sleep( twait1 )   # maybe not necessary: flush waits unitl all is written
  # using USB-RS485 converter: no echo of sent data !
  # receive answer from module
  line = ser.readline()

  try:
    line = line.decode()
  except Exception as e:
    vor.vorlaut( 2,  "10 cannot decode line")
    vor.vorlaut( 2,  "   exception = %s"%(e))
    pass

  rxCmd = rmb.unwrap_modbus( line )
  return rxCmd




