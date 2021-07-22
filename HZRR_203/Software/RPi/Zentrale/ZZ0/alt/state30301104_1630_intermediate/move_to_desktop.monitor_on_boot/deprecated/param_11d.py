#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Sun Dec 18 11:13:51 2016

@author: pl


Parameter settings for HZ-RR011c and -d


"""
#hz_rr_version = "11c"
hz_rr_version = "11d"

# *** setup variable names and values

# parameter comments 
parC = [
  [  0, 'regulator is active / used; 0: not used'],
  [  1, 'Vorlauf, switch to summer if below'], 
  [  2, 'Vorlauf, switch to winter if above'],
         
  [  3, 'Intervall fuer Regelzyklus Sommerbetrieb'],
  [  4, 'Intervall fuer Regelzyklus Winterbetrieb'],
  [  5, '<20.0 !!! Ruhezeit nach der eine Ventilbewegung ausgefuehrt wird'],
  [  6, 'time to close valve from open position for summer operation'],
  [  7, 'time to open valve from close position in winter operation'],
         
  [  8, 'time to hold valves open until normal operation continues'],
         
  [  9, 'x-Achse 1. Punkt der Kennlinie'],
  [ 10, 'y-Achse 1. Punkt der Kennlinie'],
  [ 11, 'x-Achse 2. Punkt der Kennlinie'],
  [ 12, 'y-Achse 2. Punkt der Kennlinie'],
         
  [ 13, 'Einschaltdauer fuer LEDs'],
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
  [ 24, 'anz. schnellerer Zyklen f. Test; zaehlt auf 0 runter'],
  [ 25, 'Gueltigkeit der Vorlauf Temp. von Zentrale; seriell empfangen']
]

# *** values for initialisation of one parameter set of a controller
    
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
valMin += [    20.0,   20.0,     2.0,     0.0,      0.0]
valDef += [   300.0,  300.0,     7.0,     6.0,      4.0]
valMax += [  3600.0,  600.0,    14.0,    10.0,     10.0]

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
valDef += [   40.0,   32.0,   75.0,  47.0 ]
valMax += [   60.0,   48.0,   80.0,  55.0 ]

index  += [     13,     14,     15,     16 ]
names  += ['dtLed', 'ttol', 'pFZu', 'pFAuf']
units  += [  'sec', 'degC',    'd',     'd']
valTyp += ['float','float','float', 'float']
valFst += ['%5.1f','%5.1f','%5.2f', '%5.2f']
valMin += [    0.3,    0.5,   0.00,    0.00]
valDef += [    1.0,    2.5,   0.02,    0.01]
valMax += [    3.0,    5.0,   2.00,    2.00]

index  += [     17,     18,     19,    20 ]
names  += ['dtMMn','dtMMx','IStop',  'IMn']
units  += [  'sec',  'sec',   'mA',   'mA']
valTyp += ['float','float','float','float']
valFst += ['%5.1f','%5.1f','%5.1f','%5.1f']
valMin += [    0.1,   20.0,   30.0,   3.0 ]
valDef += [    0.1,   30.0,   50.0,   5.0 ]
valMax += [    1.0,  100.0,   80.0,  10.0 ]

index  += [     21,        22 ]
names  += ['dtVoc',     'vFix']
units  += [  'sec',        'd']
valTyp += ['float',  'uint8_t']
valFst += ['%5.1f',       '%d']
valMin += [   20.0,         0 ]
valDef += [   23.0,         0 ]
valMax += [   90.0,         1 ]

index  += [       23,       24,         25 ]
names  += [   'test',    'fast','tvzTValid']
units  += [      'd',       'd',     'degC']
valTyp += ['uint8_t', 'uint8_t',    'float']
valFst += [     '%d',      '%d',    '%5.1f']
valMin += [        0,        0 ,     120.0 ]
valDef += [        0,        0 ,     600.0 ]
valMax += [        1,      255 ,     600.0 ]

