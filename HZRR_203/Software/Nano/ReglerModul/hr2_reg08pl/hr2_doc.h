
/*
 * hzrr200 Regler EEPROM read-write
 * Datei "hr2_eeprom.h"
 * 
 * 
 * 
 */


#ifndef hr2_doc_h
#define hr2_doc_h

/* 
 *  
 *  
FRAGEN AN BURKHARD DOBLINGER:
=============================
+ ok Sollwert Zimmertemperatur: 20 degC +/- 4degC ?
+ VOREINSTELLUNG (factory setting: Alle Regler ein oder aus, regler 1 auf Zimmer?
- Timing bei Zimmertemperatur Regler?
- Regelparameter factory settings durchgehen und festlegen



*/

/*  *********************
 *  ZUSÄTZLICHE LIBRARIES
 *  *********************
+ <LiquidCrystal_I2C.h>  LiquidCrystel I2C by Frank de Brabander; https://gitlab.com/tandembyte/LCD_I2C
+ "DallasTemperature.h"  Dallas Temperature, installs also OneWire library
+ "OneWire"
+ "TimerOne" 
 */

/*
Bedienung des hzrr200 Regler Moduls


Status LCD
==========
*** Tastenbelegung:
Taste SW1 -> Service LCD


Service LCD
===========
*** Tastenbelegung:
Taste SW1 -> Funktionswahl
Tasten SW2...SW4 -> Motor1 bis 3, Funktion ausführen
Taste SW5 -> Verlassen des Service Menüs

nach 10 Minuten automatisches Verlassen des Service Menüs


LCD Beleuchtung
===============
automatisch abschalten nach 10 Minuten, parametriert

























*/
#endif   //  hr2_doc_h
