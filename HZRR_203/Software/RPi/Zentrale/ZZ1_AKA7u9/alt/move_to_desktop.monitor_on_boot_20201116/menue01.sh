#!/bin/bash
PROGPATH=/home/pi/Desktop/Monitor/PYTHONUSB
PROGNAME=menue01.py
LOGFILE=$PROGPATH/log/loglog.txt
NOW=$(date +"%Y-%m-%d %H:%M:%S")

cd $PROGPATH
#python3 $PROGNAME &


#! /bin/sh
### BEGIN INIT INFO
# Startet $PROGNAME

case "$1" in
  start)
  if ps aux | grep -v grep | grep $PROGNAME > /dev/null
    then
      MSG="1: $NOW - $PROGNAME ist bereits aktiv"
      echo $MSG
      echo $MSG >> $PROGPATH/log/loglog.txt
    else 
      MSG="2: $NOW - $PROGNAME wird gestartet"
      echo $MSG
      echo $MSG >> $PROGPATH/log/loglog.txt
      python3 $PROGPATH/$PROGNAME >> $LOGFILE &
  fi
  ;;

  stat)
  if ps aux | grep -v grep | grep $PROGNAME > /dev/null
    then
      echo "5: $NOW - $PROGNAME läuft"
    else 
      echo "6: $NOW - $PROGNAME läuft nicht"
  fi
  ;;

  stop)
  if ps aux | grep -v grep | grep $PROGNAME > /dev/null
    then
      MSG="3: $NOW - $PROGNAME wird beendet"
      echo $MSG
      echo $MSG >> $LOGFILE
      pkill -f $PROGNAME
    else
      MSG="4: $NOW - $PROGNAME läuft nicht - kann es nicht beenden"
      echo $MSG
      echo $MSG >> $LOGFILE
  fi
  ;;


  *)
  echo "Usage: $0 {start|stat|stop}"
  echo "  start        start menue-program"
  echo "  stat         show status: menue-program ist running or not"
  echo "  stop         stop menue-program"
  exit 1
  ;;

esac

exit 0

