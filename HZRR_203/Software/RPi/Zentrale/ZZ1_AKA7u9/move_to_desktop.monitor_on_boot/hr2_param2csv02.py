#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
make .csv file from parameter file
'''
parFile = "parameter/paramRx.dat"
parCsvFileDP ="parameter/paramRxDP.csv"
parCsvFileCo ="parameter/paramRxCo.csv"
fin = open(parFile,"r")
fout= open(parCsvFileDP,"w")
varnames=[]
regVarnames=[]
columns=[]
regColumns=[]
modules=[]
for line in fin:
    #print(line)
    l0=line.strip()
    l1=l0.split(",")
    mod = int( l1[0].lstrip("mod"))
    reg = int( l1[1].lstrip("reg"))
    if not (mod in modules):
        modules.append(mod)
    print("mod=%d reg=%d"%(mod,reg))
    sh  = l1[0]+","+l1[1]+","
    #print(sh)
    l10 = l0.lstrip(sh)
    v1 = eval(l10)
    regspar = v1.pop("r")  # module parameters stay in v1
    modpar = v1
    
    if reg==0 :   # only module parameters
        pass
        values=[]
        for idx in modpar:
            #print(idx,modpar[idx])
            if mod == 1 :
                varnames.append(idx)
            values.append(modpar[idx])
        columns.append([mod, values])
        pass
    if  reg<=3:  # only regulator parameters; was 1<=reg<=3
        regValues=[]
        for idx in regspar[reg]:
            if mod==1 and reg==1:
                regVarnames.append(idx)
            regValues.append(regspar[reg][idx])
        regColumns.append([mod,reg,regValues])
        pass
    else:
        print("wrong module/regulator index")

fout.write('"module:";')
for col in range( len(columns)):
    fout.write(str(modules[col])+";;;;")
fout.write("\n")
    
for line in range(len(varnames)):
    fout.write(varnames[line])
    fout.write(";")
    for col in range( len(columns)):
        val=columns[col][1][line]
        fout.write(str(val))
        fout.write(";;;;")
    fout.write("\n")

fout.write("\n")
fout.write("\n")

fout.write('"mod/reg:";')
for col in range( len(columns)):
    mod = modules[col]
    fout.write("%d/0;%d/1;%d/2;%d/3;"%(mod,mod,mod,mod))
fout.write("\n")
    
for line in range( len(regVarnames)):
    fout.write(regVarnames[line])
    fout.write(";")
    for col in range( len(regColumns)):
        val=regColumns[col][2][line]
        fout.write(str(val))
        fout.write(";")
    fout.write("\n")

fin.close()
fout.close()

# *** replace decimal points with commas for German spreadsheets
fi = open(parCsvFileDP,"r")
fo = open(parCsvFileCo,"w")
for line in fi:
    l0=line.replace(".",",")
    fo.write(l0)

fi.close()
fo.close()
x=1

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
