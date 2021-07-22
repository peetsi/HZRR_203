# -*- coding: utf-8 -*-
"""
HZ-RR012

rr01_par.py

Parameter data set ralated functions

Created on Sat Nov 26 08:10:57 2016

@author: pl
"""
# parameter comments
parC = [
  [  0, 'regulator is active / used; 0: not used'],
  [  1, 'Vorlauf, switch to summer if below'],
  [  2, 'Vorlauf, switch to winter if above'],

  [  3, 'Intervall fuer Regelzyklus Sommerbetrieb'],
  [  4, 'Intervall fuer Regelzyklus Winterbetrieb'],
  [  5, '<20.0 !!! Ruhezeit nach der eine Ventilbewegung ausgef􏻼hrt wird'],
  [  6, 'time to close valve from open position for summer operation'],
  [  7, 'time to open valve from close position in winter operation'],

  [  8, 'time to hold valves open until normal operation continues'],

  [  9, 'x-Achse 1. Punkt der Kennlinie'],
  [ 10, 'y-Achse 1. Punkt der Kennlinie'],
  [ 11, 'x-Achse 2. Punkt der Kennlinie'],
  [ 12, 'y-Achse 2. Punkt der Kennlinie'],

  [ 13, 'Einschaltdauer f􏻼r LEDs'],
  [ 14, 'Toleranz; unter +/-ttol wird nicht geregelt'],
  [ 15, 'proportionalfaktor fuer Regelabweichung Ventil Zu'],
  [ 16, 'proportionalfaktor fuer Regelabweichung Ventil Auf'],

  [ 17, 'minimale Motorlaufzeit fuer Regeln'],
  [ 18, 'maximale Motorlaufzeit fuer zum auf Anschlag fahren'],
  [ 19, 'stop motor if current exceeds this value; limited to MOTOR_I_STOP'],
  [ 20, 'stop motor if current is below -> motor not connected'],

  [ 21, 'time for a valve travel from open to closed or vice versa'],
  [ 22, '0 regulate normal; 1 if valve kept open; 2 if closed;'],

  [ 23, 'testMode;'],
  [ 24, 'anz. schnellerer Zyklen f. Test; zaehlt auf 0 runter']
]

# *** values for initialisation of one parameter set of a controller
global index
global names, units, valTyp, valFst, valMin, valDef, valMax


index  = [         0,      1,     2 ]
names  = [  'active',  'tvs',  'tvw']
units  = [       'd', 'degC', 'degC']
valTyp = [ 'uint8_t','float','float']
valFst = [      '%d','%5.1f','%5.1f']
valMin = [         0,   25.0,   32.0]
valDef = [         1,   30.0,   35.0]                # default values
valMax = [         1,   45.0,   45.0]

index  += [       3,      4,       5,       6,       7 ]
names  += [   'dts',  'dtw',   'dtS', 'dtSZu', 'dtWAuf']
units  += [   'sec',  'sec',  'days',   'sec',    'sec']
valTyp += [ 'float','float', 'float', 'float',  'float']
valFst += [ '%5.1f','%5.1f', '%5.1f', '%5.1f',  '%5.1f']
valMin += [    30.0,   20.0,     2.0,     3.0,      0.0]
valDef += [   120.0,   60.0,     7.0,     6.0,      4.0]
valMax += [   600.0,  300.0,    14.0,    20.0,     10.0]

index  += [      8 ]
names  += ['dtInst']
units  += [   'sec']
valTyp += [ 'float']
valFst += [ '%5.1f']
valMin += [  120.0 ]
valDef += [  300.0 ]
valMax += [  600.0]

index  += [      9,     10,     11,    12 ]
names  += [  'tv0',  'tr0',  'tv1',  'tr1']
units  += [ 'degC', 'degC', 'degC', 'degC']
valTyp += ['float','float','float','float']
valFst += ['%5.1f','%5.1f','%5.1f','%5.1f']
valMin += [   35.0,   30.0,   65.0,  45.0 ]
valDef += [   50.0,   37.0,   75.0,  47.0 ]
valMax += [   50.0,   40.0,   80.0,  55.0 ]

index  += [     13,     14,     15,     16 ]
names  += ['dtLed', 'ttol', 'pFZu', 'pFAuf']
units  += [  'sec', 'degC',    'd',     'd']
valTyp += ['float','float','float', 'float']
valFst += ['%5.1f','%5.1f','%5.2f', '%5.2f']
valMin += [    0.3,    0.5,    0.01,    0.01]
valDef += [    1.0,    1.5,    0.1,     0.2]
valMax += [    3.0,    5.0,    3.0,     3.0]

index  += [     17,     18,     19,    20 ]
names  += ['dtMMn','dtMMx','IStop',  'IMn']
units  += [  'sec',  'sec',   'mA',   'mA']
valTyp += ['float','float','float','float']
valFst += ['%5.1f','%5.1f','%5.1f','%5.1f']
valMin += [    0.2,   20.0,   30.0,   3.0 ]
valDef += [    0.3,   40.0,   40.0,   5.0 ]
valMax += [    1.0,  100.0,   80.0,  10.0 ]

index  += [     21,        22 ]
names  += ['dtVoc',     'vFix']
units  += [  'sec',        'd']
valTyp += ['float',  'uint8_t']
valFst += ['%5.1f',       '%d']
valMin += [   20.0,         0 ]
valDef += [   23.0,         0 ]
valMax += [   90.0,         1 ]

index  += [       23,       24 ]
names  += [   'test',    'fast']
units  += [      'd',       'd']
valTyp += ['uint8_t', 'uint8_t']
valFst += [     '%d',      '%d']
valMin += [        0,        0 ]
valDef += [        0,        0 ]
valMax += [        1,        1 ]


