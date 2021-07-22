#!/bin/bash
PROGPATH=/home/pi/Desktop/Monitor/PYTHONUSB
PROGNAME=hz_rr_log_b.py
LOCKNAME=log.lock
KILLFILE01=hz_rr_monitor_direct02.py
LOGFILE=$PROGPATH/log/loglog.txt
NOW=$(date +"%Y-%m-%d %H:%M:%S")

cd $PROGPATH
#python3 $PROGNAME &


#! /bin/sh
### BEGIN INIT INFO
# Startet $PROGNAME

case "$1" in
  start)
  
  if ps aux | grep -v grep | grep $KILLFILE01 > /dev/null
  then
      MSG="20: $NOW - $KILLFILE01 beendet bevor $PROGANAME gestartet werden kann"
      echo $MSG
      echo $MSG >> $LOGFILE
      pkill -f $KILLFILE01
  fi
  


  
  if ps aux | grep -v grep | grep $PROGNAME > /dev/null
  then
      MSG="1: $NOW - $PROGNAME ist bereits aktiv"
      echo $MSG
      echo $MSG >> $LOGFILE
  else 
      MSG="2: $NOW - $PROGNAME wird gestartet"
      echo $MSG
      echo $MSG >> $LOGFILE
      python3 $PROGPATH/$PROGNAME >> $LOGFILE &
  fi
  ;;

# if a lockfile is set, data transver is needed elsewhere
# a lock-file is set to indicate this. A cron-task tries
# to start the log-program. If it finds the lock-file
# the program is not started, but the lockfile is deleted.
# next time the same command does not find the lockfile and
# starts the log-program.
# so at least for a full cron time-period the other program can
# use the serial bus for data transfer.
  startlock)
  if [ -e $LOCKNAME ]
  then
      MSG="11: $NOW - $LOCKNAME wird geloescht"
      echo $MSG
      rm $LOCKNAME
  else
      if ps aux | grep -v grep | grep $PROGNAME > /dev/null
      then
          MSG="12: $NOW - $PROGNAME ist bereits aktiv"
          echo $MSG
          echo $MSG >> $LOGFILE
      else 
          if ps aux | grep -v grep | grep $KILLFILE01 > /dev/null
          then
               MSG="21: $NOW - $KILLFILE01 beendet bevor $PROGANAME gestartet werden kann"
               echo $MSG
               echo $MSG >> $LOGFILE
               pkill -f $KILLFILE01
          fi
          MSG="13: $NOW - $PROGNAME wird gestartet"
          echo $MSG
          echo $MSG >> $LOGFILE
          python3 $PROGPATH/$PROGNAME >> $LOGFILE &
      fi
  fi
  ;;

  startsilent)
  if ps aux | grep -v grep | grep $PROGNAME > /dev/null
  then
      MSG="7: $NOW - $PROGNAME ist bereits aktiv"
      # echo $MSG
      echo $MSG >> $LOGFILE
  else 
      if ps aux | grep -v grep | grep $KILLFILE01 > /dev/null
      then
           MSG="22: $NOW - $KILLFILE01 beendet bevor $PROGANAME gestartet werden kann"
           echo $MSG
           echo $MSG >> $LOGFILE
           pkill -f $KILLFILE01
      fi
      MSG="8: $NOW - $PROGNAME wird gestartet"
      # echo $MSG
      echo $MSG >> $LOGFILE
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
  echo "Usage: $0 {start|startlock|startsilent|stat|stop}"
  echo "  start        start log-program"
  echo "  startlock    check lock-file; if present delete lock file,"
  echo "               else start log-program"
  echo "  startsilent  start log-program; no echos to console"
  echo "  stat         show status: log-program ist running or not"
  echo "  stop         stop log-program"
  echo "  all start-commands erase $KILLFILE01 before starting (if it is running)"
  exit 1
  ;;

esac

exit 0
