#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
make .csv file from parameter file
'''
import glob
import time
import os


pathParam = "parameter/"
# all input files
flist = glob.glob(pathParam+"paramRx*.dat")
flist.sort
# input files which were translated before
#flistDone = glob.glob("paramRx*.csv")

for parFile in flist:
    # parFile = "parameter/paramRx.dat"

    parCsvFileDP = parFile.rstrip(".dat")+"DP.csv"
    parCsvFileCo = parFile.rstrip(".dat")+"Co.csv"
    
    print("read %s -> \ngenerate '.' (DP) output file %s\n and convert to German file %s"%
          (parFile,parCsvFileDP,parCsvFileCo))
    fin = open(parFile,"r")
    fout= open(parCsvFileDP,"w")
    varnames=[]
    regVarnames=[]
    columns=[]
    regColumns=[]
    modules=[]
    cntLine=cntDataLine=0
    for line in fin:
        #print(line)
        cntLine += 1
        l0=line.strip()
        if l0[0] == '#' :
            continue       # skip comment
        cntDataLine += 1
        l1=l0.split(",")
        mod = int( l1[0].lstrip("mod"))
        reg = int( l1[1].lstrip("reg"))
        if not (mod in modules):
            modules.append(mod)
        print("m%02dr%d "%(mod,reg),end="")
        if cntLine % 16 == 0:
            print()
        sh  = l1[0]+","+l1[1]+","
        #print(sh)
        l10 = l0.lstrip(sh)
        if "ifferences:" in l10:
            continue
        v1 = eval(l10)
        regspar = v1.pop("r")  # module parameters stay in v1
        modpar = v1
        
        if reg==0 :   # only module parameters
            pass
            values=[]
            for idx in modpar:
                #print(idx,modpar[idx])
                if not (idx in varnames) :
                    varnames.append(idx)
                values.append(modpar[idx])
            columns.append([mod, values])
            pass
        if  reg<=3:  # only regulator parameters; was 1<=reg<=3
            regValues=[]
            for idx in regspar[reg] :
                if not (idx in regVarnames) : 
                    regVarnames.append(idx)
                regValues.append(regspar[reg][idx])
            regColumns.append([mod,reg,regValues])
            pass
        else:
            print("wrong module/regulator index")
    print()

    fout.write('"module:";')
    for col in range( len(columns)):
        fout.write(str(modules[col])+";;;;")
    fout.write("\n")
        
    cntModData=0
    for line in range(len(varnames)):
        cntModData += 1
        fout.write(varnames[line])
        fout.write(";")
        for col in range( len(columns)):
            cntModData += 1
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
        
    cntRegData=0
    for line in range( len(regVarnames)):
        cntRegData += 1
        fout.write(regVarnames[line])
        fout.write(";")
        for col in range( len(regColumns)):
            cntRegData += 1
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
    print("read lines:%d, data lines:%d, written module data:%d, regulator data:%d"%
          (cntLine,cntDataLine,cntModData,cntRegData))

