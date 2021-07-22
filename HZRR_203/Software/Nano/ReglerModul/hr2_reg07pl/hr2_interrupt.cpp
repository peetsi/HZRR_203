
// *********************************************************
// **** INTERRUPT SERVICE ROUTINE (ISR) ****  --- every msec
// *********************************************************

// --------------------------
// INCLUDES
// --------------------------

#include "hr2_interrupt.h"

// ----------------------------------------------------------------------
// *** Schieberegister (SR) Funktionen
// ----------------------------------------------------------------------

// *** erweiterete digitale I/Os
// Jene des MC reichen nicht aus. Also wurde per SPI (seriell-parallel interface) ueber 
// Schieberegister 16bit Output und 8bit Input angeschlossen.
// Die aktuell als Ausgang verwendeten Bits werden hier gespeichert:
uint16_t extended_dout;


// schiebe zwei Bytes raus und empfange ein Byte:
uint16_t spi_exchange_bytes( uint16_t tosend ) {
  // zerlege 2-Byte Werte in zwei einzelne Bytes
  union {                 // empfangene Bytes
    uint16_t rxBytes;
    byte brx[2];
  };
  union {                 // zu sendende Bytes
    uint16_t txBytes;
    byte btx[2];
  };

  txBytes = tosend;
  SPI.beginTransaction(SPISettings(10000,MSBFIRST,SPI_MODE0));  // Harware SPI

  // *** 1. shift out actual data to output SR; Daten muessen fuer Schritt 2. stimmen 
  SPI.transfer( btx[1] );  // high byte first
  SPI.transfer( btx[0] );
  
  // *** 2. read input lines to input register
  // generate a 0->1 slope:
  //   595 RCLK pin12: shiftregister -> output latches !!! shr has to have proper data !!! 
  //   597 STCP pin12: input lines -> input register
  digitalWrite(SRQ_PIN,0);
  digitalWrite(SRQ_PIN,1);

  // *** 3. move input-latched data to input shift register
  //   597: a low level loads from input latches to shift register
  digitalWrite(nPL_PIN,0);     // low level uebernimmt Daten vom Eingang ins input SR
  digitalWrite(nPL_PIN,1);     // 

  // *** 4. read 8 bit data from input register  
  // shift two bytes to make sure the output shift registers are both set 
  brx[0]=SPI.transfer( btx[1] );  // contains the output byte of the second output register
  brx[1]=SPI.transfer( btx[0] );  // contains the input lines

  SPI.endTransaction();
  return rxBytes;
}


void init_extended_digital_output( void ) {
  // Setze die Output Leitungen des SR auf Ausgangswerte:
  // Multiplexer address 0, turn off all switches, H-Bridge all outputs low, V_Therm off
  // V_Therm: switched off there is no current through the Pt1000 resistor->do not heat it
   extended_dout = 0 | HB_M0A | HB_M0B | HB_M1A | HB_M1B | HB_M2A | HB_M2B | V_THERM;
   spi_exchange_bytes( extended_dout );
}


uint8_t get_address( void ) {
  // Lies die Adresse des Moduls von den Steckbruecken ein
  // Jumper settings as on board, set jumper add up value:
  // jumper nr       :   1   2   3   4   5    (  6   7   8 )
  // value/notation  :   1   2   4   8  16    ( 32  64 128 )
  // address example 
  // jumer           :   0  set  0  set set   (special function)
  //   module address:   0 + 2 + 0 + 8 +16 = 26
  // special functions:
  // jumper 6 / notaion  32:   TBD (to be defined)
  // jumper 7 / notaion  64:   TBD
  // jumper 8 / notaion 128:   reguator 1 regulates room-temperature 
  byte jmp = ~spi_exchange_bytes( extended_dout );
  st.jumpers = jmp;
  st.modAddr = jmp & 0x1F;   // only the lower 5 bits are the address
  if( jmp & 0x20 ) { st.r[1].active = par.r[1].active; } // use parameter value
  else             { st.r[1].active = 0; } // jumper open -> inactive
  if( jmp & 0x40 ) { st.r[2].active = par.r[2].active; } // use parameter value
  else             { st.r[2].active = 0; } // jumper open -> inactive
  if( jmp & 0x80 ) { st.roomReg = true; }
  else             { st.roomReg = false; }

  return st.modAddr;
}


// *** Temperatur Sensor Multiplexer

void set_mux( byte sel ) {
  // setze die Multiplexer Adresse fuer die Temperatursensoren; bis zu 8 Sensoren
  // sel = multiplexer address 0 < sel < 7 to switch channels
  uint16_t mask;
  mask = MUX_A0 + MUX_A1 + MUX_A2 + MUX_EN;
  extended_dout = extended_dout & ~mask;  // multiplexer address = 0; disable mux;
  mask = MUX_EN;
  if( sel & 0x0001 ) mask += MUX_A0;
  if( sel & 0x0002 ) mask += MUX_A1;
  if( sel & 0x0004 ) mask += MUX_A2;
  extended_dout = extended_dout | mask;   // set mux address and enable
  spi_exchange_bytes( extended_dout );
}


// ----------------------------------------------------------------------
// TEMPERATURE SENSORS
// ----------------------------------------------------------------------

// *** Dallas DS18B20 Temperatursensoren
float read_DS18B20( byte channel ) {
  float degC;
  set_mux(channel);   // select sensor
  degC = sensors.getTempCByIndex(0);    // read new values,
  sensors.setWaitForConversion(false);        // makes it async
  sensors.requestTemperatures();              // start next conversion
  sensors.setWaitForConversion(true);
  return degC;
}


// *** Raum Thermostat 
void set_rt_supply( byte onOff ) {
  // schalte die Stromversorgung des Raumtemperatursensors ein
  // Bei Dauer-Ein erwärmt sich der Sensor, also wird er nur zur Messung eingeschaltet
  // onOff==0 -> off, !=0 -> on
  if( onOff == 0 ) {
    extended_dout |= V_THERM;
  }
  else {
    extended_dout &= ~V_THERM;
  }
  spi_exchange_bytes( extended_dout );
}


float get_room_temperature( void ) {
  // Der Raumthermostat liefert die Temperatur UND eine Betriebsart (mode) ueber den
  // Widerstand. Er entspricht immer 0 bid 51.2 Grad Celsius
  // mode 
  //   1   Automatikbetrieb, 'Uhr',    0   -  51.2 degC
  //   2   Normal (Tag)      'Sonne', 51.2 - 102.4 degC
  //   3   Absenk (Nacht)    'Mond', 102.4 - 152.6 degC
  //   4   Standby           'Punkt',152.6 - 203.8 degC
  // siehe auch #define TEMP_ROOM_x
  // mode wird bestimmt aber nicht ausgewertet
  //
  long adOutSum = 0L;
  long adRefSum = 0L;
  int i,n;

  // *** switch on thermometer supply voltage
  set_rt_supply( 1 );
  //delay(10);
  delay(1);   // wait for stable supply; 0.5msec is OK
  n=100;
  for(i=0; i<n; i++) {
    adOutSum  += analogRead(ANAIN1_PIN);
    adRefSum  += analogRead(ANAIN2_PIN);
  }
  set_rt_supply( 0 );
  float digUref=(float)adRefSum/(float)n;
  float digUout=(float)adOutSum/(float)n;
  // calculation:
  // is too complex to be documented here; separate calculation
  // in separate documentation sheet
  float alpha=0.5342;
  float beta=1.5342e-3;
  float gamma=0.002;
  // calculate amplification of 7.5
  float ux = (digUref-digUout)/7.5 + digUref;
  // calculate resistance rx of Pt1000 thermo resistor + offset;
  float rx = 1 / (digUref*beta /(ux*alpha)-gamma);  // dig->Volt compensates

  // calculate temperature from rx
  // parameters for Pt100 resitors -> use rx * 0.1
  float a3=   -5.67E-06;
  float a2=    0.0024984;
  float a1=    2.22764;
  float a0= -242.078;
  float rxh = rx*0.1;
  st.rTemp = a3*rxh*rxh*rxh + a2*rxh*rxh + a1*rxh + a0;
  if( st.rTemp > 153.6 ) {
    st.rTemp -= 153.6;
    st.rMode = TEMP_ROOM_STANDBY;
  }
  else if( st.rTemp > 102.4 ) {
    st.rTemp -= 102.4;
    st.rMode = TEMP_ROOM_NIGHT;
  }
  else if( st.rTemp > 51.2 ) {
    st.rTemp -= 51.2;
    st.rMode = TEMP_ROOM_DAY;
  }
  else {
    st.rMode = TEMP_ROOM_AUTO;
  }
  return st.rTemp;
}



// -----------------------------------------------------------
// switch / button handling
// -----------------------------------------------------------

// *** switches are handled in interrupt service routine (ISR)
//
     
// *** READ BUTTON from analog input
byte button(void){
  // safety margin +/-4%: +/-40 
  // digits:   1013 751 707 633 633 542 482 482 460 360 316 316 234 186
  // switches:    1   2  23  24 234   3  25  35  34   4  35 345  45   5
  // max       1013 791 747 673 673 582 522 522 500 400 356 356 274 226
  // min        973 711 667 593 593 502 442 442 420 320 276 276 194 146
  //             ok  xx  xx  xx  xx  ok  xx  xx  xx  ok  xx  xx  xx  ok
  int i,j;
  do{  // debounce reading two levels
    i = analogRead( SWITCH_PIN );
    delay(5);
    j = analogRead( SWITCH_PIN );
  } while( (i>>2)!=(j>>2) );        // check same value range
  byte sw=0;
  if(i>=973)        sw=1;
  else if(i>=711)   sw=2;
  else if(i>=502)   sw=3;
  else if(i>=320)   sw=4;
  else if(i>=146)   sw=5;
  st.but = sw;
  if( st.but && !st.butOld ) {       // button pressed, positive slope
    st.butPressed = st.but;
  }
  st.butOld = st.but;
  return sw;
}


byte read_button(void){
  // returns button nr. pressed, then clears button memory
  // NOTE:  actual button state is in "st.but"
  byte but = 0;
  if( st.butPressed ) {
    but = st.butPressed;
    st.butPressed = 0;
  }
  return but;
}


// -----------------------------------------------------------
// LCD 4X20 
// -----------------------------------------------------------

// *** Anzeige auf einer 4 Zeilen 20 Spalten LCD
// Das LCD wird ueber eine I2C Schnittstelle angesprochen
// Im Folgenden elementare Ein- und Ausgangsfunktionen

// set the LCD address to 0x27 for a 20 chars and 4 line display
// *** uses library LiquidCrystel I2C by Frank de Brabander ***
LiquidCrystal_I2C lcd( 0x27,20,4 );  

void init_lcd4x20(void) {
  //Serial.print(F("init LCD ..."));
  lcd.init();
  lcd.init();
  lcd.clear();
  lcd.noCursor();
  lcd.backlight();
  //Serial.println(F(" done"));  
}


void lcd_logon(byte mode) {
  lcd.clear();
  lcd.setCursor( 0, 0);   lcd.print(FIRMWARE_NAME);           // <--- wieso das so schreiben, wenns eine function mit lcd_print(col,row,char) gibt? oder bin ich doof :P -andi
  lcd.setCursor( 2, 1);   lcd.print(F("FW:"));                   // (die lcd_print ist 2 functionen unter der hier)
  lcd.setCursor( 5, 1);   lcd.print(FIRMWARE_VERSION);
  lcd.setCursor(10, 1);   lcd.print(FIRMWARE_DATE);
  lcd.setCursor( 2, 2);   lcd.print(F("HW:"));
  lcd.setCursor( 5, 2);   lcd.print(HARDWARE_VERSION);
  lcd.setCursor(10, 2);   lcd.print(HARDWARE_DATE);
  if(mode==1){
    lcd.setCursor( 0, 3);   lcd.print(F("***ERR:ADDRESSE 0***"));
    //                                   0123456789 123456789 
  }
}

void lcd_cls() {
  lcd.clear();
}

void lcd_light( byte onOff ) {
  // onOff = 0:off, else on
  if( onOff ){
    lcd.backlight();
    st.backLightEnd = millis() + (uint32_t)par.dtBackLight*60L*1000L;
  }
  else{
    lcd.noBacklight();
  }
}



// LCD Status screen
// TODO:Adresse anzeigen
// sp  01234567890123456789 
//    +--------------------+
// z0 |A000 VL  RL 11.1 eee|
// z1 |RR0:22.2 33.3 999mff|
// z2 |xx1:22.2 33.3 999mff|
// z3 |RR2:22.2 33.3 999mff|
//    +--------------------+
//     01234567890123456789
//
// A000 module address in decimal format
// 11.1 central Vorlauf temperature if available, else "    "
// xx1  e {"RR1", "ZR1"} for {Rücklauf Regler, Zimmertemp.Regler}
// 22.2 local Vorlauf temperature, always
// 33.3 local Rücklauf temperature, if regulator RRx is active
// 999  relative valve position, "  0" to "999" (in per mille)
//      if 'motor not connected': "MNC" 
// m    e {' ','*','o','c'} motor activity {none,to be started, open, closed}
// eee  module error flags (hex-bits, up to 3 nibbles, typ. )
// fff  regulator error flags (hex-bits, up to 3 nibbles)
// *    e {'r','z'} for mode {Rücklauf Regler, Zimmertemp.Regler}
void lcd_status(byte rNr){
  // rNr    regulator nr. 0,1,2, or 
  //        3  for Head-line
  char s[25];      // 21 would do - just to be sure
  char s0[6],s1[6],s2[6];
  char ma;         // motor activity

  //freemem();
  
  if(st.lcdService > 0) {
    return;                // LCD screen 'service' is active
  }
  
  switch(rNr){
    case 0:
    case 1:
    case 2:    

      // *** write line for regulator
      if(st.r[rNr].active == 0) {
        // *** motor not active
        sprintf(s0,"RR%d:",rNr);
        LCDP(0,rNr+1,s0);
        LCDP(4,rNr+1,F(" NOT ACTIVE "));
      }
      else {
        // 'RR' and 'RZ' (Regulation Rücklauf/Zimmertemp.)

        // *** show motor action
        if( st.r[rNr].motStart > 0 )    ma='*';   // marked for start
        else if( st.motRunning == rNr ) {
          if( st.motDir == MOT_CLOSE )  ma='c';   // closing
          else                          ma='o';   // opening
        }
        else{
                                        ma=' ';
        }
        
        // *** show measured VL and RL temperatures
        if( st.r[rNr].tempVl <= 0.0 ){
          strcpy( s0,"N.C." );
        }
        else{
          dtostrf(st.r[rNr].tempVl,4,1,s0);
        }
        if( st.r[rNr].tempRlMeas <= 0.0 ){
          strcpy( s1,"N.C." );
        }
        else{
          dtostrf(st.r[rNr].tempRlMeas,4,1,s1);          
        }
        
        // *** display Zimmertemp. for reg 1
        if( (rNr==1 )&&( st.roomReg ) ) {
          strcpy( s0,"ZiTh");
          dtostrf(st.rTemp,4,1,s1);
        }

        // *** valve-motor position or motor not connected
        if(st.r[rNr].motConnected == MOT_NOT_CONNECTED){
          strcpy(s2,"MNC");
        }
        else{
          dtostrf(st.r[rNr].motPos,3,0,s2);
        }
        
        if( (rNr==1 )&&( st.roomReg ) ){
          // *** patch for Zimmer temperature regulator
          s[1] = 'Z';  // should overwrite char[1]=='R' -> 'RR' ->'RZ'
        }
        
        // *** build and display LCD-line
        sprintf(s,"RR%d:%4s %4s %3s%c%2X",rNr,s0, s1, s2, ma, st.r[rNr].msg);
        // *** print line to LCD
        lcd.setCursor( 0, rNr+1);      lcd.print(s);
        //LCDP(0,rNr+1,s);
      }

    break;
    
    //    +--------------------+
    // z0 |A000 VL  RL 11.1 eee|
    // z1 |RR0:22.2 33.3 999mff|
    // z2 |xx1:22.2 33.3 999mff|
    // z3 |RR2:22.2 33.3 999mff|
    //    +--------------------+
    //     01234567890123456789
    
    case 3:       // write basic frame == headline
      if( DIFF(millis(), st.tVlRxEnd ) > 0 ) {
        strcpy(s0,"VLC-");
      }
      else {
        dtostrf(st.tempVlRx,4,1,s0);
        sprintf(s,"%4s", s0);
      }
      //         01234567890123456789
      sprintf(s,"A%03d VL  RL %s %3X",st.modAddr, s0, st.msg);
      //lcd.setCursor( 0, 0); lcd.print(s);
      LCDP(0,0,s);
    break;

    default: // some compilers need it!
    break;
  }
}



// LCD Service screen
//   but. function 
//     01234567890123456789
//    +--------------------+
// 0a |1> select           | (*0)
// 1  |2: motor0 wait      |
// 2  |3: motor1 run       |
// 3  |4: motor2      5:END| 
//    +--------------------+
//   but. function 
// Alternative pressing button 1 the line permutates:
// 0b |1> open             | (*1)
// 0c |1> close            | (*2)
// 0d |1> start position   | (*3)
// 0d |1> stop             | (*4)
// 0e |1> valve.calib      | (*5)
//  +--> goto 0a
//
byte il0=0;   // global index

void lcd_service( byte but ) {
  // service - motor - selections
  // but    0: refresh display status
  //        1..5 service action
  byte dir;


  if( but > 0 ) {
    lcd_light( true );                      // 1;     start also lcd-backlight timer
    st.smTEnd = millis() + 10L*60L*1000L;   // ms;    terminate LCD service menu after this time
  }

  if(but==9){
    lcd_cls();
    il0=0;
  }

  // *** perform button and setup (9) functions
  if( but==1 || but==9 ) {
    if( but==1 ) {
      il0++;
      if(il0>=5) il0=0;
    }
    switch(il0){
      case 0: lcd.setCursor( 0, 0); lcd.print(F("1> open      ")); break;
      case 1: lcd.setCursor( 0, 0); lcd.print(F("1> close     ")); break;
      case 2: lcd.setCursor( 0, 0); lcd.print(F("1> start pos.")); break;
      case 3: lcd.setCursor( 0, 0); lcd.print(F("1> stop      ")); break;
      case 4: lcd.setCursor( 0, 0); lcd.print(F("1> valve.cal.")); break;
    }
    lcd.setCursor( 15, 3); lcd.print(F("5:END"));
  }

  if( but==2 || but==9 ) {
    lcd.setCursor( 0, 1); lcd.print(F("2: motor0"));
    if(but==2){
      switch(il0){
        case 0: dir = MOT_OPEN; break;
        case 1: dir = MOT_CLOSE; break;
        case 2: dir = MOT_STARTPOS; break;
        case 3: dir = MOT_STOP; st.r[0].motCalib = 0; st.r[0].motPos = MOT_STOP; break;
        case 4: st.r[0].motCalib = 1; return; break; // performed in loop()
        default:dir = MOT_STOP; break;
      }
      valve_action( 0, dir, (uint32_t)((float)par.r[0].tMotMax*1000.0), false);
    }
  }

  if( but==3 || but==9 ) {
    lcd.setCursor( 0, 2); lcd.print(F("3: motor1"));
    if(but==3){
      switch(il0){
        case 0: dir = MOT_OPEN; break;
        case 1: dir = MOT_CLOSE; break;
        case 2: dir = MOT_STARTPOS; break;
        case 3: dir = MOT_STOP; st.r[1].motCalib = 0; st.r[1].motPos = MOT_STOP; break;
        case 4: st.r[1].motCalib = 1; return;  break; // performed in loop()
        default:dir = MOT_STOP; break;
      }
      valve_action( 1, dir, (uint32_t)((float)par.r[1].tMotMax*1000.0), false);
    }
  }

  if( but==4 || but==9 ) {
    lcd.setCursor( 0, 3); lcd.print(F("4: motor2"));
    if(but==4){
      switch(il0){
        case 0: dir = MOT_OPEN; break;
        case 1: dir = MOT_CLOSE; break;
        case 2: dir = MOT_STARTPOS; break;
        case 3: dir = MOT_STOP; st.r[2].motCalib = 0; st.r[0].motPos = MOT_STOP; break;
        case 4: st.r[2].motCalib = 1; return; break; // performed in loop()
        default:dir = MOT_STOP; break;
      }
      valve_action( 2, dir, (uint32_t)((float)par.r[2].tMotMax*1000.0), false);
    }
  }

  if( (but==5)||(DIFF(millis(), st.smTEnd) > 0)  ) {
    // end of lcd service-screen
    st.lcdService = 0;
    lcd.setCursor( 15, 3); lcd.print(F(" EXIT"));
        // do not use this code:
        //causes a crash - so do not activate this code
        //the motors stop after leaving the function
        //for(byte mot=0;mot<3;mot++){
        //  st.r[mot].motStart = 0;       // erase all pending tasks
        //}
        //st.motStop = 1;                 // stop current motor
        //init_var_position( 1 );         // set to known values
    valve_motor_off_all();
    delay(100);
    lcd_cls();
    return;
  }

  // *** show status information
  //Serial.println();
  for(byte mot=0;mot<3;mot++){
    lcd.setCursor( 10,mot+1 );
    if( st.r[mot].active==0 )                          {lcd.print(F("INACT"));}
    else if( st.r[mot].motConnected==MOT_NOT_CONNECTED){lcd.print(F("-MNC-"));}
    else if( st.r[mot].motStart > 0 )                  {lcd.print(F("wait "));}
    else if( st.motRunning == mot )                    {lcd.print(F("run  "));}
    else if( st.r[mot].motLimit == MOT_CLOSE)          {lcd.print(F("CLOSE"));}
    else if( st.r[mot].motLimit == MOT_OPEN)           {lcd.print(F("OPEN "));}
    else if( st.r[mot].motLimit == MOT_STARTPOS)       {lcd.print(F("StPos"));}
    else if(st.r[mot].motPos==0)                       {lcd.print(F(" --  "));}
    else                                               {lcd.print(F("     "));}
  }

  //Serial.println();
};





// ----------------------------------------------------------------------
// VALVE MOTOR 
// ----------------------------------------------------------------------

// *** Ansteuerung der Motore zur Ventilverstellung
// Um den Strombedarf zu begrenzen darf immer nur ein Motor laufen.
// Werden mehrere Verstellungen benoetigt, so muessen die Motoren nacheinander 
// eingeschaltet werden.
// Die Strommessung erfolgt gemeinsam fuer alle Motoren; 
// bei Ueberschreiten eines bestimmten Stromes wird der Motor abgeschalter 
// (Anschlag erreicht)

// motor switched directly - for test-use;
// take valve_action for normal operation using Interrupt (ISR)
void valve_motor( byte motor, byte dir ) {
  // WARNING: only ONE MOTOR shall run at the same time
  //          Andi : To do this, i have added "VALVE_MOTOR_RUNNING" - this var gets set to 1 if any motor is  running.
  //                - and while this is set to run, no other motor can run.
  //                - VALVE_MOTOR_RUNNING has to be set to 0 each time a motor is not in use  anymore - therefore im adding it into 
  //                - the control function directly.
  // motor    0..2 for one of the three motors
  // dir      MOT_STOP, MOT_CLOSE, MOT_OPEN
  uint16_t ha, hb;


  if(      motor==0 ) { ha=HB_M0A; hb=HB_M0B; }        // set H-bridge bits in SR out variable
  else if( motor==1 ) { ha=HB_M1A; hb=HB_M1B; }
  else if( motor==2 ) { ha=HB_M2A; hb=HB_M2B; }
  else                { ha=0;      hb=0; }
  
  extended_dout |= (ha + hb);                         // eq. MOT_STOP; HB-A and HB-B high -> ground on each side of motor
  
  if(      dir==MOT_CLOSE ) { extended_dout &= ~ha; } // HB-A low -> motor line becomes high, forward
  else if( dir==MOT_OPEN ) { extended_dout &= ~hb; }  // HB-B low -> other line high, reverse  
  spi_exchange_bytes( extended_dout );    

}

// switch off all valve motors - much faster than switching each off
void valve_motor_off_all(void){

  extended_dout |= (HB_M0A + HB_M0B + HB_M1A + HB_M1B + HB_M2A + HB_M2B);
  spi_exchange_bytes( extended_dout );
  // set flags back to unused motors 
  st.motRunning = MOT_FREE;
  st.motReady   = true;          // handshake for waiting functions
  st.motStop    = 0;             // make sure this flag is zero
}



byte motor_check_connected( byte ri ) {
  // ri      regulator index e {0,1,2}
  // plpl  replace by a fast motor-on / current measure function
  if( st.r[ri].active==0 ) {
    st.r[ri].motConnected = MOT_NOT_TESTED;
    return MOT_NOT_ACTIVE;
  }
  valve_action( ri, MOT_OPEN, 200L, true );    // for a short time on, blocking
  if(st.r[ri].msg & MSG_MOT_NOT_CONNECTED) {
    st.r[ri].motConnected = MOT_NOT_CONNECTED;
    return MOT_NOT_CONNECTED;
  }
  else {
    st.r[ri].motConnected = MOT_CONNECTED;
    return MOT_CONNECTED;
  }
}


void set_motor_position( byte  ri, byte direction, uint32_t dt ) {  
  // set relative motor-valve position in a range from 0 (closed) to 999 (open)
  // value can be resetted to 0 or 999 if a limit is reached
  // otherwise only relative changes are summed up (integrated)
  // this leads to an integration error, so the numer is only relative
  // useful to evaluate changes over time
  //  ri           1    regulator nr. e {0,1,2}
  // direction     1    e {MOT_OPEN, MOT_CLOSE}
  // dt            ms   motor move time

  if( st.r[ ri].motLimit == MOT_CLOSE ) {
    st.r[ ri].motPos = 0.0;
  }
  else if( st.r[ ri].motLimit == MOT_OPEN ) {
    st.r[ ri].motPos = 999.0;
  }
  else if( st.r[ ri].motLimit == MOT_STARTPOS ) {
    if(par.r[ ri].dtClose==0) {par.r[ ri].dtClose=30;} // typical value
    st.r[ ri].motPos = (int16_t)(999.0 * (float)par.r[ ri].dtOffset / ((float)par.r[ ri].dtClose * 1000.0) );
  }
  else if(dt != 0) {
    if( direction == MOT_CLOSE ) { 
      if(par.r[ ri].dtClose==0) {par.r[ ri].dtClose=30;} // typical value; avoid div/0
      st.r[ ri].motPos -= (999.0 * (float)dt / ((float)par.r[ ri].dtClose * 1000.0) );
      if( st.r[ ri].motPos < 0.0 ) { 
        st.r[ ri].motPos = 0.0;
        st.r[ ri].motLimit = MOT_CLOSE;
      }
    }
    if( direction == MOT_OPEN ) {
      if(par.r[ ri].dtOpen==0) {par.r[ ri].dtOpen=30;} // typical value; avoid div/0
      st.r[ ri].motPos += (999.0 * (float)dt / ((float)par.r[ ri].dtOpen * 1000.0 ));
      if( st.r[ ri].motPos > 999.0 ) { 
        st.r[ ri].motPos = 999.0; 
        st.r[ ri].motLimit = MOT_OPEN;
      }
    }
  }
}


// *** change valve setting via motor
// 
byte valve_action( byte mot, byte direction, uint32_t duration, bool blocking ) {
  // input:    mot  e {0,1,2}
  //           direction  e {MOT_STOP, MOT_CLOSE, MOT_OPEN, MOT_STARTPOS} 
  //           duration   msec
  //           blocking   e {}
  //      
  // return:
  //           MOT_STOP       if motor was stopped
  //           MOT_BUSY       if motor could not be started
  //           MOT_STARTED    if motor was marked to be started
  //           MOT_WRONG_DIR  if direction was wrong

  byte rv;    // return value

  if( st.r[mot].active == 0 ) {
    rv = MOT_NOT_ACTIVE;
  }

  else if( (direction!=MOT_STOP)&&(direction!=MOT_CLOSE)&&(direction!=MOT_OPEN)&&(direction!=MOT_STARTPOS) ) {
    rv = MOT_WRONG_DIR;
  }
  
  else if(direction==MOT_STOP) {
    st.motStop=1;                        // tell to stop all motors
    rv = MOT_STOP;
  }

  else if(st.r[mot].motStart > 0){
    rv = MOT_BUSY;
  }

  else{
    if(direction==MOT_STARTPOS){
      st.r[mot].motGotoStart = 1;
      direction=MOT_CLOSE;
      duration = (uint32_t)((uint32_t)par.r[mot].tMotMax * 1000L);
    }
    //noInterrupts();   // frueher: motor control was in ISR
    st.motStop            = 0;           // dont stop motor at once
    st.motReady           = false;
    st.r[mot].motReady    = false;
    st.r[mot].motDir      = direction;
    st.r[mot].tMotDur     = duration;
    st.r[mot].motLimit    = MOT_STOP;    // limit will be set in ISR if reached 
    st.r[mot].msg &= ~MSG_MOT_NOT_CONNECTED;
    // set at last - ISR will handle motor start
    st.r[mot].motStart   = 1;      // tell motor_handling(); was in ISR - now polling
    //interrupts();   // frueher: motor control was in ISR
    statist.tMotTotal[mot] += (float)duration/1000.0;
    if( blocking ) { 
      while( !(st.motReady) ){; } 
      rv = MOT_STOP;
    }
    else {
      rv = MOT_STARTED; 
    }
  }
  set_motor_position( mot, direction,  duration );
  return rv;
}



void valve_calibrate( byte mot ) {
  // valve close - open - close sequence
  // measure times and store them to eeprom parameters
  // plpl TODO test, fertig machen

  switch(st.r[mot].motCalib){
    case 0: return;
    break;

    case 1:
      valve_action( mot, MOT_CLOSE, (uint32_t)((float)par.r[0].tMotMax*1000.0), false);
      st.r[mot].motCalib++;
    break;
    
    case 2:
      if( st.r[mot].motReady ) {
        valve_action( mot, MOT_OPEN, (uint32_t)((float)par.r[0].tMotMax*1000.0), false);
        st.r[mot].tStart = millis();
        st.r[mot].motCalib++;
      }
    break;
    
    case 3:
      if( st.r[mot].motReady ) {
        par.r[mot].dtOpen  = (uint8_t)( (millis() - st.r[mot].tStart)/1000);
        valve_action( mot, MOT_CLOSE, (uint32_t)((float)par.r[0].tMotMax*1000.0), false);
        st.r[mot].tStart = millis();
        st.r[mot].motCalib++;
      }
    break;
    
    case 4:
      if( st.r[mot].motReady ) {
        st.r[mot].motCalib=0;
        par.r[mot].dtClose  = (uint8_t)( (millis() - st.r[mot].tStart)/1000);
        //eeprom_put_parameter( EEPROM_PARAMETER_ADDRESS );    // TODO remove for production
      }
    break;
  }
}








// *** measure motor current from analog input
float motor_current(void) {
  // Messe den Motorstrom
  // ATTENTION:
  //   + Dauer dieser Funktion < 0.3 msec !!!   -   muss in Zeitrahmen passen !
  //   + only one motor is activated at the same time. 
  //   + The current is measured over all motors
  //   + a delay of peak-motor-current evaluation is performed in interrupt (ISR)
  // *** calculation of current in mA
  // amplified by 4.3; voltage at 3.3Ohm resistor; ADC reference = 5V ->
  // measured value in Volt:         mv[mV]  = 5000[mV] * digval(adc) / 1023; 
  // voltage over 3.3Ohm resistor:   rv[mV]  = mv[mV] / 4.3;       // amplification
  // current through 3.3Ohm resitor: ri[mA]  = rv[mV] / 3.3[Ohm];  // Ohm's law
  // => ri = digval(adc) / ADC_RANGE * 5000.0 / 4.3 / 3.3 = digval(adc) / ADC_RANGE * 352.36

  st.adMot2 = analogRead( Vmot2_PIN );         // half the motor supply voltage: 3.3V / 2 = 1.65V typ.
  st.motAD = analogRead(  MOTCURR_PIN );
  st.motUsV  = 10.0 * st.adMot2 / ADC_RANGE;   // nominal 3.3V; Vref is Vs of controller -> 5V
  st.motImA = 356.36 * (float)st.motAD / (float)ADC_RANGE;
  //st.motImALP = 0.25 * st.motImA + 0.75 * st.motImAOld;
  //st.motImAOld= st.motImA;
  //SPR(" I.mot=",st.motImA);
  return st.motImA;
}




// *** switch off current motor
void motor_off( uint8_t mot) {
  // mot     motor index (nr. 0,1,2)
  valve_motor_off_all();
  st.motReady = true;         // handshake for waiting functions
  st.r[mot].motReady = true;  // handshake for waiting functions
  st.motStop = 0;             // make sure this flag is zero
  st.r[mot].motConnected = MOT_CONNECTED;      // assume motor is connected
  st.r[mot].msg &= ~MSG_MOT_NOT_CONNECTED;     // clear flag
  //Serial.print(F(" st.motImA="));
  //Serial.print(st.motImA);
  //Serial.print(F(""));
  if( st.motImA < (float)st.motIMin ) {
    //Serial.print(F(" nc"));
    st.r[mot].motConnected = MOT_NOT_CONNECTED;
    st.r[mot].motLimit = MOT_NOT_CONNECTED;
    st.r[mot].msg |= MSG_MOT_NOT_CONNECTED;      // set flag
    if( st.r[mot].motGotoStart > 0 ) {
      st.r[mot].motGotoStart = 0;      // cannot goto startpos. if no motor present
    }
  }
  else if( st.motImA < (float)st.motIMax ) {
    //Serial.print(F(" normal"));
    // normal drive - no limit reached
    if( st.r[mot].motGotoStart == 2 ) {
      st.r[mot].motLimit = MOT_STARTPOS;
      st.r[mot].motGotoStart = 0;
    }
    else{
      st.r[mot].motLimit = MOT_STOP;
    }
    st.r[mot].motConnected = MOT_CONNECTED;
    st.r[mot].msg &= ~MSG_MOT_NOT_CONNECTED;     // clear flag
  }
  else{
    //Serial.print(F(" limit"));
    // limit reached because of high current
    st.r[mot].motLimit = st.r[mot].motDir;
    st.r[mot].motConnected = MOT_CONNECTED;
    st.r[mot].msg &= ~MSG_MOT_NOT_CONNECTED;     // clear flag
    set_motor_position( mot, st.r[mot].motDir, 0L );
    statist.nMotLimit[mot]++;
  }
  //Serial.print(F(" mot="));
  //Serial.print(mot);
  //Serial.print(F(" motLimit="));
  //Serial.println(st.r[mot].motLimit);

}



void motor_handling( void ){
  uint8_t mot;     // motor index e {0,1,2}

  if( st.motRunning == MOT_FREE ) {
    // *** find a motor to start if there is a request pending
    mot=0;
    do {
      if( st.r[mot].active > 0 ) {
        if( (st.r[mot].motStart != 0)&&(st.motRunning==MOT_FREE) ) {
          // ein Motor soll gestartet werden
          st.r[mot].motConnected = MOT_NOT_TESTED;// motor start determines if connected 
          st.motRunning   = mot;                  // Nr. 0,1,2 des laufenden Motors
          st.motIMin      = par.r[mot].motIMin;   // zum Vergleich waehrend des Laufs
          st.motIMax      = par.r[mot].motIMax;   // zum Vergleich waehrend des Laufs
          st.motDir       = st.r[mot].motDir;     // direction
          st.tMotDelayEnd = millis() + par.r[mot].tMotDelay; // skip higher motor-on current
          st.motReady     = false;
          st.r[mot].motReady = false;             // handshake for waiting functions
          st.tMotEnd      = millis() + st.r[mot].tMotDur;   // (NOW + DURATION) time-end "max" time
          valve_motor( mot, st.motDir );          // start + direction[open/close]
          st.r[mot].motStart=0;                   // reset start-motor trigger
          mot=99;   // end of do-loop; keine weitere Suche da nur 1 Motor laufen darf
        }
      }
      mot++;
    } while( mot < 3 );
  }
  else{ // one motor is running
    // *** switch off current motor if requested
    mot = st.motRunning;                                 // index of running motor 0,1,2
    if(mot != MOT_FREE){
      // motor_current(); // measured in tic_action()
      if( st.motStop > 0 ){                              // stop flag is set
        st.r[mot].motCalib=0;
        st.r[mot].motGotoStart=0;
        motor_off(mot);
      }        
      else if(DIFF(millis(),st.tMotEnd) >= 0 ){          // motor Laufzeit erreicht
        motor_off(mot);
      }
      else if(DIFF(millis(),st.tMotDelayEnd) > 0) {      // skip motor-on current peak
        if( st.motImA > (float)st.motIMax ) {            // limit reached
          motor_off(mot);
        }
        else if( st.motImA < (float)st.motIMin ) {       // no motor connected
          motor_off(mot);
        }        
      }
    }
  }
}





// Tasks:
//   + starts and stops one motor, controlled completely by status variables st.xxx
//   + reads button switches
//   + measures motor current

void tic_action(void){
  if( st.tic==0 ) return;
  else{
    //SPRL(" tic=",st.tic);
    button();
    motor_current();
    motor_handling();
    st.tic=0;
  }
}












// **********************************************************************************
// ***************** interrupt service routine (ISR) and functions ******************
// **********************************************************************************

// -----------------------------------------
// *** functions alled from motor2limitINT()
// -----------------------------------------




// **** ATTENTIION: timer1 affects PWM Pins 9 and 10 -> PWM on Pin 9 is nolonger usable 
// is called every msec; 
void  tic_INT(void) {
  rs485_readln();      // receive command and serial data if available
  st.tic++;
}

// *********************************************************
// *********************************************************
