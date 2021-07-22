''' 
hr2_net_var.py
'''


# *****************************
# global variables

# settings
testMotors  = [(1,1),(1,3)]

# internal use
motCurrent = 0
hostname = ""
tempPath = "temp/"
filename = ""
motTestFilename = None

# *** parameter names
#  0   1  2    3    4    5    6  7    8   9 + "r"
# 10,120,10,40.0,75.0,32.0,46.0,30,20.0,0.5,
parModNames=[
    "timer1Tic","tMeas","dtBackLight",\
    "tv0","tv1","tr0","tr1","tVlRxValid",\
    "tempZiSoll","tempZiTol","r"
]

parRegNames=[\
    # c5: 0 1  2  3   4  5  6  7    8   9
    #     1,5,70,80,100,40,28,34,3000,500,
    [ "active","motIMin","motIMax","tMotDelay",\
        "tMotMin","tMotMax","dtOpen","dtClose",\
        "dtOffset","dtOpenBit"],\
    # c6:   10    11    12   13   14   15
    #    0.100,0.000,0.000,1.00,1.00,1.00,
    [ "pFakt","iFakt","dFakt","tauTempVl","tauTempRl","tauM"],\
    # c7:    16      17  18  19   20   21    22
    #    50.000,-50.000,600,900,2000,2000,2.000,
    [ "m2hi","m2lo","tMotPause","tMotBoost","dtMotBoost",\
    "dtMotBoostBack","tempTol"]\
    #"tMotTotal","nMotLimit" are sent with status2 - cmd 4
]



# *** error flag definition
RXE_SHORT     = 0x0001  # received string is too short
RXE_VALUE     = 0x0002  # wrong value
RXE_HEADER    = 0x0004  # wrong header format
RXE_ADR       = 0x0008  # wrong/not matching answer address
RXE_CMD       = 0x0010  # wrong/not matching command
RXE_MOD       = 0x0020  # wrong/not matching module number
RXE_REG       = 0x0040  # wrong/not matching regulator
RXE_PROT      = 0x0080  # unknown protocol version
RXE_CHECK     = 0x0100  # wrong checksum or RLL
RXE_NAK       = 0x0200  # no acknkwledge
RXE_TX_TOUT   = 0x0400  # timeout sending command
RXE_TX_SEREX  = 0x0800  # serial Tx exception
RXE_TX_EXCEPT = 0x0800  # generat serial Tx exception
RXE_RX_TOUT   = 0x1000  # timeout receiving command
RXE_RX_SEREX  = 0x2000  # serial Tx exception
RXE_RX_EXCEPT = 0x2000  # generat serial Tx exception
RXE_RX_CODE   = 0x4000  # encode-decode error in string

