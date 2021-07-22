'''
hr2_net_serial.py

serial network communication via RS485 bus
New Version from Jan.2021, pl

Changes:
--------
- Improved timing:
  occasionally a module des not switch off
  transmit-state immediately after the last
  byte sent -> bus is blocked
  workaround:
  a delay of 13msec was added before a new command
  can be sent from the master (this program)
  This speeds up communication 
  tests gave 100,000s of error free data xfers
- check each answer with command given for
  correct module, regulator and command-nr and
  raise an error if the answer does not fit

'''


# **************************************
# Serial Port settings
#

serTimeout = 0.5
serialPort_PIthree = "/dev/serial/by-path/platform-3f980000.usb-usb-0:1.1.3:1.0-port0"
serialPort_PIfour  = "/dev/serial/by-path/platform-fd500000.pcie-pci-0000:01:00.0-usb-0:1.4:1.0-port0"
# select serial port depending on installed Raspberry Pi:
serPort = serialPort_PIfour
br = 115200

def ser_instant() :
    ser = None
    err=0
    try:
        ser = serial.Serial(
            port        = serPort,
            baudrate    = br,
            parity      = serial.PARITY_NONE,
            stopbits    = serial.STOPBITS_TWO,
            bytesize    = serial.EIGHTBITS,
            timeout     = serTimeout,
            write_timeout=serTimeout
            )
    except serial.SerialException as e:
        print( 3,  "01 cannot find: %s"%(serPort))
        print( 3,  "   exception = %s"%(e))
        err = 1
    except Exception as e:
        print( 3,  "02 something else is wrong with serial port: %s"%(serPort))
        print( 3,  "   exception = %s"%(e))
        err = 2
    return err, ser


def ser_open(ser):
    err=0
    try:
        ser.open() # open USB->RS485 connection
    except serial.SerialException as e:
        print( 3,  "03 cannot open: %s"%(serPort))
        print( 3,  "   exception = %s"%(e))
        err = 3
    except  Exception as e:
        print( 3,  "04 something else is wrong with serial port:"%(serPort))
        print( 3,  "   exception = %s"%(e))
        err = 4
    return err


def ser_check():
    err = 0
    err,ser = ser_instant()
    if (err==0):
        if (ser.isOpen() == False) :
            err = ser_open(ser)
            if( err ) :
                print("rs485 Netz nicht verbunden: %d"%(err))
                return err,ser
            else:
                print("rs485 Netz geoeffnet")
            time.sleep(0.1)
        print("rs485 Netz verbunden")
    return err, ser




def txrx_Command_2( txCmd ):
    err=0
    rxDatB = None
    rxDat  = None
    # NOTE wait some time to make sure the bus is released
    #      by other modules
    #      on zz0 with 2 modules 0.1s still lead to errors
    #      0.13 sec seemed to perform well
    time.sleep(0.13)  # 0.1 makes timeout errors zz0
    if type(txCmd)==str :
        txCmd = txCmd.encode()  # byte-array needed for serial comm.
    ser.reset_input_buffer()
    #ser.reset_output_buffer()
    #print("send command:",txCmd)
    try:
        ser.write(txCmd)       # send command
    except serial.SerialTimeoutException as e:  # only for tx timout !!!
        err |= RXE_TX_TOUT
        print(e)
        return err, rxDat
    except serial.SerialException as e:
        err |= RXE_TX_SEREX
        print(e)
        return err, rxDat
    except Exception as e:
        err |= RXE_TX_EXCEPT
        print(e)
        return err, rxDat
    # ??? not needed? ser.flush()  # send out tx-buffer 
    ser.flush()
    #while ser.out_waiting : # block until whole command is sent
    #    pass

    #time.sleep(0.05)
    tbeg = time.time()
    try:
        rxDatB = ser.readline()
    except serial.SerialException as e:
        err |= RXE_RX_SEREX
        print(e)
    except Exception as e:
        err |= RXE_RX_EXCEPT
        print(e)
    tend = time.time()
    to = ser.get_settings()["timeout"]
    if (tend-tbeg) > to:  # timeout occurred
        err |= RXE_RX_TOUT
        print("RX timeout")

    if rxDatB != None:
        try:
            rxDat = rxDatB.decode()
        except UnicodeDecodeError as e:
            rxDat = ""
            print(e)
            err |= RXE_RX_CODE
        except Exception as e:
            rxDat = ""
            print(e)
            err |= RXE_RX_CODE
    return err,rxDat

