#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
make .csv file from parameter file
'''
parFile = "parameter/paramRx.dat"
parCsvFile ="parameter/paramRx.csv"
fin = open(parFile,"r")
fout= open(parCsvFile,"w")
for line in fin:
    #print(line)
    l0=line.strip()
    l1=l0.split(",")
    mod = int( l1[0].lstrip("mod"))
    reg = int( l1[1].lstrip("reg"))
    print("mod=%d reg=%d"%(mod,reg))
    sh  = l1[0]+l1[1]
    print(sh)
    l10 = l0.lstrip(sh)
    pass

'''    
mod30,reg3,
{'timer1Tic': 10.0, 'tMeas': 120.0, 'dtBackLight': 10.0, 'tv0': 40.0, 'tv1': 75.0, 
 'tr0': 43.0, 'tr1': 46.0, 'tVlRxValid': 30.0, 'tempZiSoll': 20.0, 'tempZiTol': 0.5, 
 'r': 
 [{'active': 1.0, 'motIMin': 5.0, 'motIMax': 70.0, 'tMotDelay': 80.0, 'tMotMin': 100.0,
   'tMotMax': 40.0, 'dtOpen': 28.0, 'dtClose': 34.0, 'dtOffset': 3000.0, 'dtOpenBit': 500.0, 
   'tMotTotal': 0.1, 'nMotLimit': 1, 'pFakt': 0.1, 'iFakt': 0.0, 'dFakt': 0.0, 
   'tauTempVl': 1.0, 'tauTempRl': 1.0, 'tauM': 1.0, 'm2hi': 50.0, 'm2lo': -50.0, 
   'tMotPause': 600.0, 'tMotBoost': 900.0, 'dtMotBoost': 2000.0, 'dtMotBoostBack': 2000.0, 
   'tempTol': 2.0}, {'active': 1.0, 'motIMin': 5.0, 'motIMax': 70.0, 'tMotDelay': 80.0, 
   'tMotMin': 100.0, 'tMotMax': 40.0, 'dtOpen': 28.0, 'dtClose': 34.0, 'dtOffset': 3000.0, 
   'dtOpenBit': 500.0, 'tMotTotal': 0.1, 'nMotLimit': 1, 'pFakt': 0.1, 'iFakt': 0.0, 
   'dFakt': 0.0, 'tauTempVl': 1.0, 'tauTempRl': 1.0, 'tauM': 1.0, 'm2hi': 50.0, 
   'm2lo': -50.0, 'tMotPause': 600.0, 'tMotBoost': 900.0, 'dtMotBoost': 2000.0, 
   'dtMotBoostBack': 2000.0, 'tempTol': 2.0}, 
  {'active': 1.0, 'motIMin': 5.0, 'motIMax': 70.0, 'tMotDelay': 80.0, 'tMotMin': 100.0, 
   'tMotMax': 40.0, 'dtOpen': 28.0, 'dtClose': 34.0, 'dtOffset': 3000.0, 'dtOpenBit': 500.0, 
   'tMotTotal': 0.1, 'nMotLimit': 1, 'pFakt': 0.1, 'iFakt': 0.0, 'dFakt': 0.0, 
   'tauTempVl': 1.0, 'tauTempRl': 1.0, 'tauM': 1.0, 'm2hi': 50.0, 'm2lo': -50.0, 
   'tMotPause': 600.0, 'tMotBoost': 900.0, 'dtMotBoost': 2000.0, 'dtMotBoostBack': 2000.0, 
   'tempTol': 2.0}, {'active': 1.0, 'motIMin': 5.0, 'motIMax': 70.0, 'tMotDelay': 80.0, 
   'tMotMin': 100.0, 'tMotMax': 40.0, 'dtOpen': 28.0, 'dtClose': 34.0, 'dtOffset': 3000.0, 
   'dtOpenBit': 500.0, 'tMotTotal': 0.1, 'nMotLimit': 1, 'pFakt': 0.1, 'iFakt': 0.0, 
   'dFakt': 0.0, 'tauTempVl': 1.0, 'tauTempRl': 1.0, 'tauM': 1.0, 'm2hi': 50.0, 
   'm2lo': -50.0, 'tMotPause': 600.0, 'tMotBoost': 900.0, 'dtMotBoost': 2000.0, 
   'dtMotBoostBack': 2000.0, 'tempTol': 2.0}
  ]
}
'''
