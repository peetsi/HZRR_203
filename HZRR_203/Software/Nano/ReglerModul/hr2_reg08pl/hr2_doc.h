
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
- Timing bei Zimmertemperatur Regler?
- Regelparameter factory settings durchgehen und festlegen



*/

/*  *************************
 *  CHANGE ON VERSION UPDATES
 *  *************************
 *  see file "hr2_regler.h" and change version 
 *  Name, revision number, date for software and hardware as required
 */

/*  *********************
 *  ZUSÄTZLICHE LIBRARIES
 *  *********************
 *  see: hr2_reg0Xpl.ino
 */

/*  *******************************
 *  PROGRAMMIERUNG DES ARDUINO NANO
 *  *******************************
 *  The program uses almost the whole FLASH meory of the AtMega328 uC.
 *  Make sure the new bootloader for the Arduino Nano is installed:
 *  1. install new bootloader on Nano if needed:
 *    1.1. use an ISP programmer, e.g. Atmel ISP Mk2 or ArduinoISP
 *         (can be wired and loaded to e.g. an Arduino Nano,
 *         examples 11. ArduinoISP; wire and program it)
 *    1.2. select from Tools (Werkzeuge): 
 *         - Board: "Arduino Nano"
 *         - Controller: "ATmega328P" (NOT old Bootlaoder!!!)
 *         - USB Port to which the ISP programmer is connected
 *         - Programmer: <select your ISP programmer>
 *    1.3. Start Tools (Werkzeuge) -> burn bootloader (Bootloader brennen) 
 *    
 *    2. program the "hr2" Software:
 *      2.1. - connect the Nano to USB port, 
 *           - select Board, Processor and Port;
 *           - program as usual with "upload" button, Sketch->Upload, or Ctrl-U
 *      2.2. If the ISP programmer is connected, you can use it instead
 *           - connect and setup as described in 1.2.
 *           - upload using programmer (Hochladen mit Programmer), or Shift-Ctrl-U
 */


/*  *********************************
    Bedienung des hzrr200 Regler Moduls
    ***********************************

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
