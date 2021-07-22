# *** read commands
#modules=[1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,30]
modules=[1]
for mod in modules:
#for reg in [0,1,2,3]:
for reg in [1] : #[1,3]:
pass
'''
#print("1 - ping(%d) = %s"% (mod, ping(mod)))
#time.sleep(3)
#print("2+4 - read_stat(module) =", read_stat(mod,reg))

# *** get parameters test
#print("*** 567-0 - get_param(mod,0) =", get_param(mod, 0))
#p = parameters[mod-1].copy()
#p.pop("r","r not available")
#print("len=",len(parameters[mod-1]),len(p))
#print( p )
#print("*** 567-1 - get_param(mod,1) =", get_param(mod, reg))
#print( parameters[mod-1]['r'][reg] )
#print("*** 567-1 - get_param(mod,1) =", get_param(mod, 1))

'''
# *** Aendere REGLER Parameter
# 1. lies Parameter von den Reglern ein
us.get_param(mod,reg)
print("Mod:%d Reg:%d"%(mod,reg),end=" ")
#print(parameter["r"][reg-1])
paramOld = copy.deepcopy(parameter)

# 2. Aendere gewuenschte Parameter
print("pFakt vom Modul=%.3f"%(float(parameter["r"][reg-1]["pFakt"])),end="; ")
parameter["r"][reg-1]["pFakt"] = 0.03
print("neu=%.3f"%(float(parameter["r"][reg-1]["pFakt"])),end="; ")

# 3. Sende Parameter an Moul-Regler
us.send_param(mod,reg)
print("neu=%.3f"%(float(parameter["r"][reg-1]["pFakt"])),end="; ")
paramNeu = copy.deepcopy(parameter)

# 4. lies Wert zur Überprüfung zurück
us.get_param(mod,reg)
print("Mod:%d Reg:%d"%(mod,reg),end="; ")
if parameter != paramOld :
print("Alte und Neue Parameter sind unterschiedlich")
if parameter == paramNeu :
print("Neue Parameter wurden übernommen")


print()

'''


# *** set commands
#print("0x20 - send_Tvor(module) =", send_Tvor(mod, 44.4))
#print("0x22 - send_param(module,0) =", send_param(mod,0))
#print("0x22 - send_param(module,1) =", send_param(mod,1))

#print("0x25 - set_motor_lifetime_status(module,reg) =", \
# set_motor_lifetime_status(mod,reg))

#print("0x30 - factory settings =",set_factory_settings(mod))

# close
#print("0x31 - close valve =",us.valve_move(mod, reg,3000, 0))
# open
print("0x31 - open valve =",us.valve_move(mod, reg,20000, 1))
# start position
#print("0x31 - startp. valve =",us.valve_move(mod, reg, 3000, 2))
#print("0x31 - startp. valve =",us.valve_move(mod, 1, 6000, 2))
#print("0x31 - startp. valve =",us.valve_move(mod, 1, 3000, 2))
#print("0x31 - startp. valve =",us.valve_move(mod, 2, 3000, 2))
#print("0x31 - startp. valve =",us.valve_move(mod, 3, 3000, 2))
#print("0x34 - set normal operation =",set_normal_operation(mod))
#print("0x35 - set reg. inactive =",set_regulator_active(mod,3,0))
#print("0x35 - set reg. inactive =",set_regulator_active(mod,reg,0))
#time.sleep(1)
#print("0x35 - set reg. active =",set_regulator_active(mod,reg,1))
#time.sleep(1)
#print("0x36 - fastmode =",set_fast_mode(mod,1))
#print("0x36 - fastmode =",set_fast_mode(mod,0))
#print("0x37 - get_millisec =",get_milisec(mod))
#print("0x38 - cpy_eep2ram=",cpy_eep2ram(mod))
#print("0x39 - cpy_ram2eep=",cpy_ram2eep(mod))
#print("0x3A - wd_halt_reset=",wd_halt_reset(mod))
#print("0x3B - clr_eep=",clr_eep(mod))
#print("0x3C - check_motor=",check_motor(mod,reg))
#print("0x3D - calib_valve=",calib_valve(modAdr,reg))
#print("0x3E - motor_off=",motor_off(modAdr,reg))
#print("0x3F - get_motor_current=",get_motor_current(mod))
#print("0x40 - lcd_backlight=",lcd_backlight(mod,0))
#time.sleep(1)
#print("0x40 - lcd_backlight=",lcd_backlight(mod,1))
#print("0x41 - jumper setting=",get_jumpers(mod))
'''

print("close network")
ser.close()

# *****************************************
# ** module communication commands **
# *****************************************

def ping( modAdr ):
txCmd = mb.wrap_modbus( modAdr, 1, 0, "" ) # cmd==1: send ping
return net_dialog(txCmd, 1)

def read_stat( modAdr, subAdr ) :
''' read all status values from module
using command 2 and 4
'''
# modAdr e {1..31}
# subAdr e {0..3} for {module, reg0, reg1, reg2}

# *** first part, scan to cn2
txCmd = mb.wrap_modbus( modAdr, 2, subAdr, "" )
if not net_dialog(txCmd):
return False
time.sleep(0.5)

# *** second part, scan to cn4
txCmd = mb.wrap_modbus( modAdr, 4, subAdr, "" )
if not net_dialog(txCmd):
return False

#read_stat(mod,reg) # result is in cn2 and cn4
get_milisec(modAdr)
get_jumpers(modAdr)

# *** print data
#print("="*40)
#print("cn2=",cn2)
#print("cn4=",cn4)
#print("timestamp ms=",st.rxMillis)
#print("Jumper settings=%02x"%(st.jumpers))
#print("-"*40)


# module data:
cmdHead = "0002%02X%db "%(modAdr,subAdr)
tic = float(st.rxMillis) / 1000.0
ticStr = "t%.1f "%(tic)

#cn2={"SN":0,"VM":0,"RM":0,"VE":0,"RE":0,"RS":0,"PM":0}
vlMeas = float(cn2["VM"])
rlMeas = float(cn2["RM"])
vlEff = float(cn2["VE"])
rlEff = float(cn2["RE"])
rlSoll = float(cn2["RS"])
posMot = float(cn2["PM"])

#cn4={"ER":0,"FX":0,"MT":0,"NL":0} # command names
erFlag = int(cn4["ER"])
fixPos = float(cn4["FX"])
motTime = float(cn4["MT"])
nLimit = int(cn4["NL"])


s1 = "VM%5.1f RM%5.1f VE%5.1f RE%5.1f "%(vlMeas,rlMeas,vlEff,rlEff)
s2 = "RS%5.1f P%03.0f "%(rlSoll, posMot)
s3 = "E%04X FX%.0f M%.0f A%d"%(erFlag,fixPos,motTime,nLimit)
# FX muss noch übersetzt werden.
x = s1 + s2 + s3
s = str(cmdHead) + str(ticStr) + str(cn2["SN"]) + " " + str(x)

print (s)

return s


def get_param(modAdr,subAdr):
'''read module-related parameter set from module'''
if subAdr in [0,1,2,3]:
txCmd = mb.wrap_modbus( modAdr, 0x05, subAdr,"" )
if not net_dialog(txCmd):
return False
elif subAdr == 0:
return True

txCmd = mb.wrap_modbus( modAdr, 0x06, subAdr,"" )
if not net_dialog(txCmd):
return False

txCmd = mb.wrap_modbus( modAdr, 0x07, subAdr,"" )
if net_dialog(txCmd):
return True

return False


def send_Tvor(modAdr,tempSend):
'''send Vorlauftemperatur to module'''
txCmd = mb.wrap_modbus(modAdr,0x20,0,','+str(tempSend)+',')
if net_dialog(txCmd):
return True
return False


def send_param(modAdr,subAdr):
''' send module parameters to module nr. modAdr
0: module, 1,2,3: regulator
'''
if subAdr == 0:
'''
// 1 2 3 4 5 6
// 1234567890123456789012345678901234567890123456789012345678901234
// :02200b 111 222 33 44.4 55.5 66.6 77.7 88 99.9 0.5 02634Ccl0" max. length
e.g.: 010 060 10 40.0 75.0 32.0 46.0 15 20.0 0.5
// with: typ.value use
// :02200b header; placeholder
// 111 10 ms; timer1Tic;
// 222 60 sec; tMeas; measruring interval
// 33 10 min; dtBackLight; time for backlight on after keypressed
// 44.4 degC; tv0; Kurve
// 55.5 degC; tv1
// 66.6 degC; tr0
// 77.7 degC; tr1
// 88 15 min; tVlRxValid
// 99.9 20 degC; tempZiSoll
// 0.5 0.5 degC; tempTolRoom
// 02634Ccl0 trailer - placeholder; cl0=="\r\n\0" (end of line / string)
'''
p = parameters[modAdr]
print("p=",p)
time.sleep(1)
# ATTENTION!!! send <tVlRxValid> 2x due to error in Nano-Software which needs it twice
s = ",%03d,%03d,%02d,%4.1f,%4.1f,%4.1f,%4.1f,%02d,%02d,%4.1f,%3.1f,"%( \
p["timer1Tic"], p["tMeas"], p["dtBackLight"], p["tv0"], \
p["tv1"], p["tr0"], p["tr1"], p["tVlRxValid"], p["tVlRxValid"], \
p["tempZiSoll"], p["tempZiTol"] )
print("*** s=",s)

txCmd = mb.wrap_modbus( modAdr, 0x22, subAdr, s )
#print(txCmd)
if net_dialog(txCmd):
return True
return False

elif subAdr in [1,2,3]: # parameter regulator, part 1,2,3
# send:
# active, motIMin, motIMax, tMotDelay, tMotMin, tMotMax,
# dtOpen, dtClose, dtOffset
time.sleep(0.2)
ps = parameters[modAdr]["r"][subAdr]
s = ",%d,%d,%d,%d,%d,%d,%d,%d,%d,"%(\
ps["active"], ps["motIMin"], ps["motIMax"], ps["tMotDelay"],\
ps["tMotMin"], ps["tMotMax"],\
ps["dtOpen"], ps["dtClose"], ps["dtOffset"] )
#print("s=",s)
txCmd = mb.wrap_modbus( modAdr, 0x22, subAdr, s )
#print(txCmd)
if not net_dialog(txCmd):
return False

# send:
# pFakt, iFakt, dFakt, tauTempVl, tauTempRl, tauM
time.sleep(0.2)
s = ",%5.3f,%5.3f,%5.3f,%6.2f,%6.2f,%6.2f,"%(\
ps["pFakt"], ps["iFakt"], ps["dFakt"], ps["tauTempVl"],\
ps["tauTempRl"], ps["tauM"] )
#print("s=",s)
txCmd = mb.wrap_modbus( modAdr, 0x23, subAdr, s )
#print(txCmd)
if not net_dialog(txCmd):
return False

# send:
# m2hi, m2lo,
# tMotPause, tMotBoost, dtMotBoost, dtMotBoostBack, tempTol
time.sleep(0.2)
s = ",%5.3f,%5.3f,%d,%d,%d,%d,%3.1f,"%(\
ps["m2hi"], ps["m2lo"], ps["tMotPause"], ps["tMotBoost"],\
ps["dtMotBoost"], ps["dtMotBoostBack"], ps["tempTol"] )
#print("s=",s)
txCmd = mb.wrap_modbus( modAdr, 0x24, subAdr, s )
#print(txCmd)
if net_dialog(txCmd):
return True
return False


def set_motor_lifetime_status(modAdr,subAdr):
''' send the regulator motor lifetime status values to module nr. modAdr
subAdr 1,2,3: regulator 1,2,3, reg-index 0,1,2,
'''
if subAdr in [1,2,3]: # parameter regulator
# send:
# tMotTotal, nMotLimit
ps = parameters[modAdr]["r"][subAdr]
s = ",%3.1f,%d,"%(ps["tMotTotal"], ps["nMotLimit"] )
#print("s=",s)
txCmd = mb.wrap_modbus( modAdr, 0x25, subAdr, s )
#print(txCmd)
#print(txCmd)
if net_dialog(txCmd) :
return True
return False


def set_factory_settings(modAdr):
txCmd = mb.wrap_modbus( modAdr, 0x30, 0, "" )
print(txCmd)
if net_dialog(txCmd):
return True
return False


def set_regulator_active( modAdr, subAdr, onOff ):
# onOff 0: switch off, 1: switch on
if onOff != 0:
onOff = 1
s = ",%d,"%( onOff )
txCmd = mb.wrap_modbus( modAdr, 0x35, subAdr, s )
if net_dialog(txCmd):
return True
return False



def valve_move(modAdr, subAdr, duration, direct):
# duration ms; motor-on time
# dir 1; 0:close, 1:open, 2:startpos
if subAdr in [1,2,3]:
s = ",%d,%d,"%(duration,direct)
txCmd = mb.wrap_modbus( modAdr, 0x31, subAdr, s )
if net_dialog(txCmd):
return True
return False


def set_normal_operation(modAdr):
txCmd = mb.wrap_modbus( modAdr, 0x34, 0, "" )
if net_dialog(txCmd):
return True
return False


def set_fast_mode( modAdr, mode ):
# onOff 0: normal mode, else: fast operation
s = ",%d,"%( mode )
txCmd = mb.wrap_modbus( modAdr, 0x36, 0, s )
if net_dialog(txCmd):
return True
return False


def get_milisec(modAdr):
txCmd = mb.wrap_modbus( modAdr, 0x37, 0, "" )
if net_dialog(txCmd):
return True
return False


def cpy_eep2ram(modAdr):
txCmd = mb.wrap_modbus( modAdr, 0x38, 0, "" )
if net_dialog(txCmd):
return True
return False

def cpy_ram2eep(modAdr):
txCmd = mb.wrap_modbus( modAdr, 0x39, 0, "" )
if net_dialog(txCmd):
return True
return False

def wd_halt_reset(modAdr):
txCmd = mb.wrap_modbus( modAdr, 0x3A, 0, "" )
if net_dialog(txCmd):
return True
return False

def clr_eep(modAdr):
txCmd = mb.wrap_modbus( modAdr, 0x3B, 0, "" )
if net_dialog(txCmd):
return True
return False

def check_motor(modAdr,subAdr):
txCmd = mb.wrap_modbus( modAdr, 0x3C, subAdr, "" )
print("check_motor, txCmd=",txCmd)
if net_dialog(txCmd):
return True
return False

def calib_valve(modAdr,subAdr):
txCmd = mb.wrap_modbus( modAdr, 0x3D, subAdr, "" )
if net_dialog(txCmd):
return True
return False

def motor_off(modAdr,subAdr):
txCmd = mb.wrap_modbus( modAdr, 0x3E, subAdr, "" )
if net_dialog(txCmd):
return True
return False

def get_motor_current(modAdr):
txCmd = mb.wrap_modbus( modAdr, 0x3F, 0, "" )
if net_dialog(txCmd):
return True
return False

def lcd_backlight(modAdr, onOff):
if onOff:
s=",1,"
else:
s=",0,"
txCmd = mb.wrap_modbus( modAdr, 0x40, 0, s )
if net_dialog(txCmd):
return True
return False

def get_jumpers(modAdr):
txCmd = mb.wrap_modbus( modAdr, 0x41, 0, "" )
if net_dialog(txCmd):
return True
return False