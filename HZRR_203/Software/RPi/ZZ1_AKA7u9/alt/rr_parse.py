#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jan 11 21:51:16 2017

@author: pl
"""

# old log file data set format
# 20170110_172715 0101 :0002011a t1813989.6  W VM 61.8 RM 47.2 VE 61.8 RE 47.2 RS 41.7 P018 E0000 FX0 M5133 A704

# new log file data set format
# change: HKx in front of ':'
# 20170111_200810 0101 HK1 :0002011a t1910046.5  W VM 56.5 RM 33.7 VE 56.5 RE 33.7 RS 39.6 P020 E0000 FX0 M5394 A706

# data set structure:
# ':' defines two parts:
#     left part:  from 'Zentrale' added data
#     right part: from module retreived data
#

import time

# ------- functions

def get_value_float( token, string, maxlen ) :
    # if maxlen == 0 -> read until next blank
    pos1 = string.find(token) + len(token)
    while string[pos1] == " " :
        # find first character
        pos1 += 1
    pos2 = pos1
    while pos2 < len(string) and string[pos2] != " " :
        # find end of value string
        pos2 += 1
    if pos2 > pos1+maxlen :
        pos2 = pos1+maxlen
    s1 = string[pos1:pos2]
    #if token == " M":
    #    print("pos1=%d; pos2=%d; maxlen=%d; s1=%s;token=%s; in string=%s"%(pos1,pos2,maxlen,s1,token,string))

    return float(s1)


def get_value_hex( token, string, maxlen ) :
    # if maxlen == 0 -> read until next blank
    pos1 = string.find(token) + len(token)
    pos2 = pos1
    while pos2 < len(string) and string[pos2] != " " :
        # find end of value string
        pos2 += 1
    if pos2 > pos1+maxlen :
        pos2 = pos1+maxlen
    s1 = string[pos1:pos2]
    #print("pos1=%d; s1=%s; token=%s; in string=%s"%(pos1,s1,token,string))
    return int(s1, base=16)



# ----- parse one line from hz_rr module -----

def rr_parse( dataset ) :
    dset0 = dataset.strip()           # remove linefeed etc
    dset1 = dset0.split(":")        # zentrale and module part

    err = 0
    if len(dset0) < 80 :  # too view data
        err = 1
        return (1,err)

    # dZen = typically
    # '20170110_172715 0101 '      (old version)
    # '20170111_200810 0101 HK1 '  (new version)
    dZen0 = dset1[0]  # Zentrale part
    # dMod = typically
    # '0002011a t1813989.6  W VM 61.8 RM 47.2 VE 61.8 RE 47.2 RS 41.7 P018 E0000 FX0 M5133 A704'
    dMod0 = dset1[1]  # module   part



    # parse Zentrale part
    # -------------------

    # ['20170110_172715', '0101', '']          (old)
    # ['20170111_200810', '0101', 'HK1', '']   (new)

    # get date and time of data set (Z-time)
    dZen1 = dZen0.split(" ")
    try:
        hstr = dZen1[0]                 # date and time
        zDateSec = time.mktime( time.strptime(hstr,"%Y%m%d_%H%M%S") )
    except Exception as e:
        err = 2
        print(e)
        return (1,err)

    # '0101' is module number and command; is also contained in module data set
    # is not evaluated here

    # try to retrieve "Heizkreis" number after "HK" string (new)
    try:
        hstr = dZen1[2]
        if hstr != "":
            hkr = int(hstr[2:])
        else :
            hkr = -1
    except Exception as e:
        err = 3
        print(e)
        return (1,err)



    # parse module part
    # -----------------

    # '0002011a t1813989.6  W VM 61.8 RM 47.2 VE 61.8 RE 47.2 RS 41.7 P018 E0000 FX0 M5133 A704'

    # parse first block:
    #   module nr     e  {0x01..0x1E} = {1..30}
    #   command nr    e  {0x01 .. 0xFF}, command and controller number
    #   controller nr e  {0,1,2,3,4},   0: module related; else: controller nr.
    #   protocol vers.e  {a,b,c,...}
    try:
        dMod1 = dMod0[0:8]
        #print(dMod1)
        command  =  int( dMod1[2:4],base=16)
        module   =  int( dMod1[4:6],base=16)
        control  =  int( dMod1[6:7])
        protVer  =  dMod1[7]
    except Exception as e:
        err = 4
        print(e)
        return (1,err)

    # timestamp from module: seconds since last reset or power up of module
    modTStamp = get_value_float( " t", dMod0, 15 )
    #print(modTStamp)

    # find summer / winter mode
    if " W " in dMod0:
        summer = 0
    elif " S " in dMod0:
        summer = 1
    else:
        summer = -1            # error
        err = 5
        return (1,err)

    dMod1 = dMod0[ dMod0.find(" VM") : ]    # use only trailing string to speed up

    # get tmperature values
    try:
        vlm = get_value_float( " VM", dMod1, 15 )  # Vorlauf, measured
        rlm = get_value_float( " RM", dMod1, 15 )  # Ruecklauf, measured
        vle = get_value_float( " VE", dMod1, 15 )  # Vorlauf, evaluation
        rle = get_value_float( " RE", dMod1, 15 )  # Ruecklauf, evaluation
        rls = get_value_float( " RS", dMod1, 15 )  # Ruecklauf, set value
        ven = get_value_float( " P",  dMod1, 15 )  # valve setting, ca. percent
        err = get_value_hex(   " E",  dMod1,  5 )  # status label (e.g. error)
        fix = get_value_float( " FX", dMod1, 15 )  # 0:variable; else valve in fixed pos.
        tmo = get_value_float( " M",  dMod1, 15 )  # sec; motor running time since power up
        tan = get_value_float( " A",  dMod1, 15 )  # count of limits reached (Anschlag)
    except Exception as e:
        err = 6
        print(e)
        return (1,err)

    #print(zDateSec,hkr,module,command,control,protVer,modTStamp,summer,
    #      vlm,rlm,vle,rle,rls,ven,err,fix,tmo,tan)
    return(zDateSec,hkr,module,command,control,protVer,modTStamp,summer,
           vlm,rlm,vle,rle,rls,ven,err,fix,tmo,tan)



# ----- main -----


# test:
if __name__ == "__main__" :
    dold = "20170110_172715 0101 :0002011a t1813989.6  W VM 61.8 RM 47.2 VE 61.8 RE 47.2 RS 41.7 P018 E0000 FX0 M5133 A704"
    dnew = "20170111_200810 0101 HK1 :0002011a t1910046.5  W VM 56.5 RM 33.7 VE 56.5 RE 33.7 RS 39.6 P020 E0000 FX0 M5394 A706"

    dset = dold
    a1=rr_parse( dset )
    print("a1=",a1)

    dset = dnew
    a2=rr_parse( dset )
    print("a2=",a2)

    a3=rr_parse( "xxx" )
    print("a3=",a3)

