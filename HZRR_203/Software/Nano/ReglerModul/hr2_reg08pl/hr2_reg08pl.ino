/*
hzrr200 Rücklaufregelung
Modul: Regler
history:
date       version   author(s)     change
2020-07-17   1.00    pl            initial version
2021-07-22   1.10    pl            added: new command Nr. 9: "answer rev.Nr."
                                   p-factor changed from 0.1 to 0.03 factory setting

*/

// *********************************************************
// @note  install Modules:  TimerOne.h
// *********************************************************
// TimerOne.h               (Tools -> Manage Libraries ...)
// LiquidCrystal_I2C.h      (Tools -> Manage Libraries ...)
//                (LiquidCrystel I2C by Frank de Brabander)
// DallasTemperature.h      (Tools -> Manage Libraries ...)
// OneWire.h              (installs with DallasTemperature)


// *********************************************************
// *********************************************************
// +++ TODO +++ TODO +++ TODO +++ TODO +++ TODO +++ TODO +++
// *********************************************************
// - save statistic regularily e.g. every day to eeprom 
//       save statistic to eeprom in intervals and get back after boot
// - cl:Plausibilitätskontrolle Temperaturen
// - check eeprom without overwriting parameter (if enough memory)
// - fast-mode for test
// - test millis()-timer turnaround by setting it to a high 0xFFFFxxxx value
// - tMeas auf 60sec ?? oder Burkh. setzen
// - motor_connected() umschreiben auf kurzen Puls mit sofortiger Strom-Messung
// *********************************************************
// *********************************************************
// TODO: patch in hr1_comm.cpp !!
//
// Zeile 633: tVlRxValid   wird 2x eingelesen -> Speicherfehler
// Workaround in RPi-python file usb_ser_b.py mit doppeltem
//   Senden dieser Variablen korrigieren !!!
// *********************************************************
// *********************************************************

// --------------------------
// INCLUDES
// --------------------------
#include "hr2_regler.h"


// --------------------------
// CLASSES
// --------------------------

OneWire oneWire( OW_PIN );
DallasTemperature sensors( &oneWire );



// --------------------------
// VARIABLES, GLOBAL
// --------------------------
status_t st;
parameter_t par;
statistic_t     statist;


// --------------------------
// SYSTEM FUNCTIONS
// --------------------------

// *** return the number of bytes currently free in RAM      
int freemem(void) { 
  extern int  __bss_end; 
  extern int  *__brkval; 
  int free_memory; 
  if((int)__brkval == 0) 
    free_memory = ((int)&free_memory) - ((int)&__bss_end); 
  else 
    free_memory = ((int)&free_memory) - ((int)__brkval); 
  //SPRL(F("freemem="),free_memory); 
  Serial.print(F("freemem=")); 
  Serial.println(free_memory);
  return free_memory;
} 



// ******************************
// *** application functions
// ******************************


// --------------------------
// FUNCTIONS for regulator
// --------------------------

// calculate Ruecklauf temperature from given Vorlauf temperature
// following a polygon shaped characteristic curve (Kennlinie)
// determined by a lint through the points from (tv0,tr0) to (tv1,tr1) 
//
// tr1|- - - - - - - +-----
//    |             /:
//    |           /  :
//  y |- - - - -+    :
//    |       / :    :
// tr0|----+/   :    :
//    |    :    :    :
//    |    :    :    :
//    +---------+----------
//       tv0   tv   tv1
// 
float characteristic( float tv ) {   
    // input:
    //      tv Vorlauf temperature to be used
    //      status_t    st     (global)
    //      parameter_t par    (global)
    // return: 
    //      set value of Ruecklauf temperature (Sollwert)
    //      set st.cs[valve].tRSet (global)
    float m,y;
      
    // *** calculate Ruecklauftemperatur from Vorlauftemperatur using characteristic curve
    if     ( tv <= par.tv0 ) y = par.tr0;               // minimum tr0
    else if( tv >= par.tv1 ) y = par.tr1;               // maximum tr1
    else {
        m = (par.tr1 - par.tr0) / (par.tv1 - par.tv0);  // slope of line (Steigung)
        y = m * ( tv - par.tv0 ) + par.tr0;             // Sollwert Ruecklauftemperatur
        st.tempRlSoll = y;                              // set result in status
     }
     return y;
}




// Low-pass filter
// iir-filter 1st order
float filterLP( float x, float yalt, float tau, float dt ) {
  float fakt = dt / tau;      // filter factor
  if(fakt>1.0) fakt = 1.0;    
  float yneu = x * fakt + yalt * (1.0 - fakt);
  return yneu;
}






// *** Rücklauf-Temperatur Regler / Zimmertemperatur Regler
//     ATTENTION: temperature values have to be measured before calling this routine
byte regler( byte reg ) {
  
  // perform regulator functions and trigger motor action
  // input
  //         reg     regulator index e {0,1,2} for regulator {1,2,3}
  //         status structure st.xxx
  //         parameter structure par.xxx
  // output  to st.yyy
  // 
  bool  motMove = true;
  float dK   = 0.0;   // Kelvin;   temp. difference - initialized at->pl
  float dtP;          // sec;      valve action time from P-factor
  float dtI;          // sec;      valve action time from D-factor
  float dtD;          // sec;      valve action time from D-factor
  float dtT;          // sec;      valve action time total
  float soll = 0.0;   // K;        temperature set value
  float ist  = 0.0;   // K;        temperature due value
  float tol  = 1.0;   // K;        tempertaure tolerance
  byte dir=MOT_STOP;

  //SPR(F("regler: reg="),reg);
  //SPRL(F(" ms="),millis());
  if(st.r[reg].active==0) {
    return 1;
  }
  
  // *** select Vorlauf temp.
  //     if time of a valid received Vorlauf temperature is active
  //     use temp. "received from master"
  //     CHANGED: otherwise use temp. "locally measured"
  //     Due to Burkhard: use 70degC
  if( DIFF(millis(), st.tVlRxEnd) > 0 ){       // received Vorlauf Value expired:
    //st.r[reg].tempVl = st.r[reg].tempVlMeas;   // use locally measured Vorlauf temperature
    st.r[reg].tempVl = 70.0;          // a high fixed value
  }
  else {
    st.r[reg].tempVl = st.tempVlRx;            // use central Vorlauf temperature
  }

  // *** no regulation if measured temperatures out of range (< -9.9)
  if( (reg == 1) && (st.roomReg == 1) ) {
    // room regulator / Zimmertermperatur
    //SPRL(F(" rTemp="),st.rTemp);
    if( (st.rTemp < 0.0) || (st.rTemp > 50.0) ){  
      return 2; 
    }
  }
  else{
    if( (st.r[reg].tempVl <= 0.0)||(st.r[reg].tempVl > 110.0) ){
      return 2;
    }
    if( (st.r[reg].tempRlMeas <= 0.0)||(st.r[reg].tempRlMeas > 110.0) ){
      return 3;
    }
  }
  

  // *** NOTE: regulation also if motor is not connected
  //     motor connection can only be detected when motor moves
  //     no movement -> unconnected motor stays unconnected for all time!

  // -------------------------------------
  // *** start regulation pre-calculations


  if( st.r[reg].firstLoop ) {
    // --------------------------------------
    // *** initialize variables on first loop
    //     actual measurements were taken before
    if((reg==1) && st.roomReg){
      st.r[reg].tempRlMeas= st.rTemp;
    }
    st.r[reg].tempVlLP1   = st.r[reg].tempVl;     // degC;   effective Vorlauf temperature
    st.r[reg].tempRlLP1   = st.r[reg].tempRlMeas; // degC;   Vorlauf temp. after 1st order lowpass
    st.r[reg].tempRlLP2   = st.r[reg].tempRlMeas; // degC;   Vorlauf temp. after 2nd order lowpass
    st.r[reg].tempRlLP2Old= st.r[reg].tempRlMeas; // degC;   previous value to determine slope
    st.r[reg].dKSum       = 0.0;
    st.r[reg].mRl         = 0.0;
    st.r[reg].mPauseEnd   = millis();
    st.r[reg].mPause      = false;
    st.r[reg].motBoostEnd = millis();
    st.r[reg].motBoost    = false;
    //
    st.r[reg].firstLoop = false;
  }

  else{
    // -----------------------
    // *** all following loops
    // *** use room-temp. in place of Ruecklauf temp if Jumper 128 is set
    if((reg==1) && st.roomReg){
      st.r[reg].tempRlMeas = st.rTemp;
    }




    // *** low-pass filter to measured values
    st.r[reg].tempVlLP1 = filterLP( st.r[reg].tempVl,    st.r[reg].tempVlLP1, par.r[reg].tauTempVl, (float)par.tMeas);
    st.r[reg].tempRlLP1 = filterLP( st.r[reg].tempRlMeas,st.r[reg].tempRlLP1, par.r[reg].tauTempRl, (float)par.tMeas);
    st.r[reg].tempRlLP2 = filterLP( st.r[reg].tempRlLP1, st.r[reg].tempRlLP2, par.r[reg].tauTempRl, (float)par.tMeas);
    //SPR(F(" VlLP1="),st.r[reg].tempVlLP1);
    //SPR(F(" tempRlLP1="),st.r[reg].tempRlLP1);
    //SPR(F(" tempRlLP2="),st.r[reg].tempRlLP2);
    // *** Vorlauf temperature too low: Summer operation - no regulation
    if( st.r[reg].tempVlLP1 < par.tv0 - 5.0 ) {
      st.r[reg].season = 'S';
      // return 5;   // plpl zum Test ausblenden
    }
    else{
      st.r[reg].season = 'W';
    }
 
    // *** find slope m of Ruecklauf temperature
    float dTempRl  = st.r[reg].tempRlLP2 - st.r[reg].tempRlLP2Old;
    st.r[reg].tempRlLP2Old = st.r[reg].tempRlLP2;
    st.r[reg].mRl = dTempRl / (float)par.tMeas;         // K / sec; slope
    st.r[reg].mRlLP1 = filterLP(st.r[reg].mRl, st.r[reg].mRlLP1, par.r[reg].tauM, (float)par.tMeas);
    //SPR(F(" mRl="),st.r[reg].mRl);
    //SPR(F(" mRlLP1"),st.r[reg].mRlLP1);

    // *** too steep up-slope: start a motor-valve pause
    if( st.r[reg].mRlLP1 > par.r[reg].m2hi / 1000.0 ){
      // restart as lang as slope is too high
      st.r[reg].mPauseEnd = millis() + (uint32_t)par.r[reg].tMotPause * 1000L;
      st.r[reg].mPause = true;
    }
    //SPR(F(" mPauseEnd="),st.r[reg].mPauseEnd);
    //SPR(F(" mPause"),st.r[reg].mPause);

    // handle end-of-pause due to steep m
    if( DIFF(millis(), st.r[reg].mPauseEnd) > 0 ) {
      st.r[reg].mPauseEnd = millis() - 1;  // drag end-time to avoid wrap-around errors
      st.r[reg].mPause = false;
    }

    // drag end-of-pause time to avoid wrap-around errors
    if( !st.r[reg].mPause ){
      st.r[reg].mPauseEnd = millis() - 1;
    }
    

    // *>*>*> from here on motor moves are performed
    //        NOTE: only one motor movement shall be invoked from the following cases
    
    // *** too steep down-slope: open valve a bit to increase circulation
    //     ATTENTION: moves motor-valve only ONCE at the beginning and end of boost-time!!
    
    // start boost-time if not yet active and too steep negative slope
    if( ( !st.r[reg].motBoost )&&( st.r[reg].mRlLP1 < par.r[reg].m2lo * 1000.0) ){
      if( st.r[reg].motStart == 0 ) {
        // there is no earlier motor start command pending:
        st.r[reg].motBoost = true;
        st.r[reg].motBoostEnd = millis() + (uint32_t)par.r[reg].tMotBoost * 1000L;
        if( !( (reg==1) && st.roomReg ) ){
          // no room-regulator: open valve a bit
          valve_action( reg, MOT_OPEN, (uint32_t)par.r[reg].dtMotBoost, false );
        }
      }
    }
    //SPR(F(" motBoost="),st.r[reg].motBoost);
    //SPRL(F(" motBoostEnd="),st.r[reg].motBoostEnd);

    // end boost-time
    if( ( st.r[reg].motBoost )&&( DIFF(millis(), st.r[reg].motBoostEnd) > 0 ) ) {
      if( st.r[reg].motStart == 0 ) {
        // there is no earlier motor start command pending:
        st.r[reg].motBoost = false;
        if( !( (reg==1) && st.roomReg ) ){
          // no room-regulator: close valve a bit
          valve_action( reg, MOT_CLOSE, (uint32_t)par.r[reg].dtMotBoostBack, false );
        }
      }
    }
    
    // drag end-of-boost time to avoid wrap-around errors
    if( !st.r[reg].motBoost ){
      st.r[reg].motBoostEnd = millis() - 1;
    }
    
    // *** close-limit reached: open valve a bit to start position
    if( st.r[reg].motLimit == MOT_CLOSE ) {
      valve_action( reg, MOT_OPEN, (uint32_t)par.r[reg].dtOpenBit, false );
    }
    
    // --------------
    // *** regulation
    // --------------
    //     ATTENTION: move motor only if Pause or Boost is NOT active 
    
    // *** define set and real value (Soll- und Ist-Wert)
    if((reg==1) && st.roomReg){
      // regulate room-temperature
      soll = par.tempZiSoll;
      st.r[reg].tempSoll = soll;
      ist  = st.r[reg].tempRlLP2;   // st.rTemp was injected above
      tol  = par.tempZiTol  ;
    }
    else {
      // regulate Ruecklauf
      soll = characteristic( st.r[reg].tempVlLP1 );
      st.r[reg].tempSoll = soll;
      ist  = st.r[reg].tempRlLP2;
      tol  = par.r[reg].tempTol;
    }
    //SPR(F(" soll="),soll);
    //SPR(F(" ist="),ist);
    //SPR(F(" tol="),tol);
    
    // *** calculate difference exceeding tolerance
    if( ist > soll + tol ) {               // higher than temp. tolerance
      dK     = (ist - soll - tol);         // (positive) difference above upper limit
      dir=MOT_CLOSE;
    }
    else if( ist < soll - tol ) {          // lower than temp. tolerance
      dK     = (ist - soll + tol);         // (negative) difference below lower limit
      dir=MOT_OPEN;
    }
    else {
      // within tolerance - do not move motor
      motMove=false;                                   // inside tolerance band
    }
    //SPR(F(" dK="),dK);
    //SPR(F(" dir="),dir);


    // *** valve-motor moving time (Stellzeit)
    st.r[reg].dKSum  += dK * (float)par.tMeas;            // integral of difference * dt
    // PID calculation
    dtP    = dK                * par.r[reg].pFakt;        // proportional part
    dtI    = st.r[reg].dKSum   * par.r[reg].iFakt;        // integral part
    dtD    = st.r[reg].mRlLP1  * par.r[reg].dFakt;        // differential part
    dtT    = dtP + dtI + dtD;
    //SPR(F(" dtP="),dtP);
    //SPR(F(" dtT="),dtT);

    // *** no motor movements during pause or boost time
    if( ( st.r[reg].mPause )||( st.r[reg].motBoost ) ) {
      motMove = false;
    }
    //SPR(F(" motMove="),motMove);

    if( motMove ) {
      st.r[reg].tMotDur = labs( (int32_t)(dtT * 1000.0) );
      if(   ( st.r[reg].motStart == 0)                // no earlier motor start command pending:
          &&( st.r[reg].tMotDur > (uint32_t)par.r[reg].tMotMin )  // minimum motor-on time exceeded
          &&  motMove
        ) {  
        valve_action( reg, dir, st.r[reg].tMotDur, false );
        //SPR(F(" tMotDur="),st.r[reg].tMotDur);
        //SPRL(F("<"),0);
      }
    }
  }
  return 0;
}







// ----------------------------
// TEMPERATURE FUNCTIONS
// ----------------------------


// read a temperature, next function call read next temperature
// will be called from main-loop with every pass
// reduces loop-time 
void read_temperature(void){
  // read temperatures sequentially
  // NOTE:
  //        takes very long; so only one temperature is read
  //        each time a different temperature
  // timings:
  //   msec  task
  //     4   DS-10B18 not connected
  //   750   DS-20B18 start - wait - read value
  //    25   read analog room-sensor
  //   
  float temp;
  
  if( DIFF(millis(),st.tDs18b20End) > 0 ) {
    st.iTemp++;
    if( st.iTemp > 6 ) st.iTemp = 0;
    st.tDs18b20End = millis() + 1000;  // set end of conversion time
    if( st.iTemp == 6 ) {
      temp=get_room_temperature();
    }
    else{
      byte reg = st.iTemp / 2;
      if(st.r[reg].active){          // read only temperatures from active regulators
        temp = read_DS18B20( st.iTemp );
        if( (st.iTemp % 2)==0 ) { st.r[reg].tempVlMeas = temp; }
        else                    { st.r[reg].tempRlMeas = temp; }
      }
    }
    //SPR(F(" temp["),st.iTemp);
    //SPRL(F("]="),temp);
  }
  return;
}


// ----------------------------
// FUNCTIONS for initialisation
// ----------------------------
void init_hardware_io(void){
  
}


void init_var_messages(void){

}



// ******************************
// *** Microcontroller HW setup
// ******************************
void mc_hardware_setup(void){
  
}



void setup() {
  pinMode(SCK_PIN, OUTPUT);    digitalWrite(SCK_PIN, 0);
  pinMode(SRQ_PIN, OUTPUT);    digitalWrite(SRQ_PIN, 0);    // 74HC575 Pin12: RCLK; register clock
  pinMode(nPL_PIN, OUTPUT);    digitalWrite(nPL_PIN, 1);    // 74HC597 Pin13: /PL (parallel load)
  pinMode(DE485_PIN, OUTPUT);  digitalWrite(DE485_PIN, 0);  // set RS485 driver to input 'read data'

  Serial.begin(115200,SERIAL_8N2);
  while(!Serial);
  SPI.begin();

  #ifdef TEST
  Serial.print(F("\nhzrr200"));
  freemem();
  #endif
    
  init_hardware_io();

  #if EEPROM_CLEAR == 1
    eeprom_clear();
  #endif
  
  get_parameter();
  init_var_status();
  init_var_messages();
  init_var_position(0);

  sensors.begin();   // one-wire dallas temp. sensors

  Timer1.initialize( par.timer1Tic * 1000L );    // micro-sec period
  Timer1.attachInterrupt(tic_INT);

  init_lcd4x20();
  
  mc_hardware_setup();

  get_address();
  lcd_light( true );   // start also lcd-backlight timer
  if(st.modAddr==0) {
    lcd_logon(1);
  }
  else {
    lcd_logon(0);
  }
  // *** read temperatures in advance to make values stable
  for( int i=0; i<7; i++ ){ read_temperature(); }  // start conversion
  delay(1000);
  for( int i=0; i<7; i++ ){ read_temperature(); }  // read currupted values, start again
  delay(1000);
  for( int i=0; i<7; i++ ){ read_temperature(); }  // read currupted values, start again

  lcd_cls();
  st.tLcdRefresh = millis() + LCD_REFRESH;
  
  Serial.print(F("\nsetup: ")); freemem();
  //SPRL(F("size par="),sizeof(par));

  statist.nBoot++;
  st.tNextMeas = millis();    // start immediately with measurements

  // *** trigger "goto valve-startposition"
  for(byte mi=0;mi<3;mi++){
    valve_action( mi, MOT_STARTPOS, (uint32_t)((float)par.r[0].tMotMax*1000.0), false);
    st.r[mi].firstLoop = true;
  }

  // *** system last functions(s)  
  // ATTENTION: hangs with "Old Bootloader" on Nano
  // installed Optiboot
  wdt_enable(WDTO_8S);

  // *** real-environment tests:
  //show_param();

}



// *****************
// *** main-loop ***
// *****************

void loop() {
  byte ri=0;
  byte but=0;
  byte mot=0;

  st.wdKey = 0;
  
  // *** perform all urgent tasks
  tic_action();
  st.wdKey |= WD_TIC_ACTION;

  // *** sequentially read temperatures at each loop
  read_temperature();        // next temperature - 7 calls for complete scan
  
  // *** LCD status or service screen
  if( DIFF(millis(), st.tLcdRefresh) > 0 ) {
    st.tLcdRefresh = millis() + LCD_REFRESH;
    // *** button switches and LCD service screen
    but = read_button();  
    get_address();
    st.wdKey |= WD_GET_ADDRESS;
    if(st.modAddr==0) {
      lcd_logon(1);  // show address error
      st.tLcdRefresh += 2000;
      st.wdKey |= WD_LCD_DISPLAY;   // same key as in lcd service-mode
    } 
    else{
      if( (but==1) && !st.lcdService ){
        st.lcdService = 1;
        lcd_service( 9 );   // setup service lcd
      }
      if( st.lcdService==0 ){
        // status lcd 
        lcd_status(3);              // head line
        for(ri=0;ri<3;ri++) {
          lcd_status(ri);          // reg.lines
          st.wdKey |= WD_LCD_DISPLAY;   // same key as in lcd service-mode
        }
      }
      else{
        // service lcd
        lcd_service( but );
        st.wdKey |= WD_LCD_DISPLAY;   // same key as in status lcd mode
      }
      but=0;
    }
    st.wdKey |= WD_LCD_REFRESH;           // is met in a short period
  }

  // *** check for next regulation time
  if( DIFF(millis(), st.tNextMeas) >= 0 ) {
    st.tNextMeas = millis() + (uint32_t)par.tMeas * 1000L;
    //SPR(F(" tMEas="),(uint32_t)par.tMeas * 1000L);
    //SPRL(F(" tNextMeas="),st.tNextMeas);
    if( st.modAddr !=0 ) {
      for(ri=0;ri<3;ri++){
        //SPR(F("loop: ri="),ri);
        //SPR(F(" lcdService="),st.lcdService);
        //SPR(F(" motGotoStart="),st.r[ri].motGotoStart);
        //SPRL(F(" motCalib="),st.r[ri].motCalib);
        if( !st.lcdService && !st.r[ri].motGotoStart && !st.r[ri].motCalib ){
          byte rvr = regler(ri);
          //SPRL(F(" rvr="),rvr);
        }
        //Serial.println();
      }
    }
  }



  // *** goto start position if flag is set
  for(mot=0;mot<3;mot++){
    if( (st.r[mot].motGotoStart == 1)&&(st.r[mot].motReady) ){
      byte rv;
      rv=valve_action( mot, MOT_OPEN, (uint32_t)par.r[mot].dtOffset, false );
      if(rv==MOT_STARTED) {
        st.r[mot].motGotoStart = 2;
      }
    }
  }

  // *** perform calibration of motor-valve timescommand
  for(mot=0;mot<3;mot++){
    valve_calibrate(mot);
  }

  // *** handle command
  if( st.modAddr != 0 ) {
    if( st.rxCmdReady ) {    // command ready
      // execute command    
      if( modbus_unwrap() == MB_ADR_OK ){
        SPR(F("loop: st.rxAdr="),st.rxAdr);
        SPR(F(" st.rxCmdNr="),st.rxCmdNr);
        SPRL(F(" st.rxReg="),st.rxReg);
        parse_cmd();
      }
      st.rxCmdReady = 0;            // ready for new command
      st.rxCmdLen = 0;              // start at index 0
      st.rxBuf[0] = 0;
    }
  }  
  
  if( DIFF(millis(), st.smTEnd) > 0  ) {
    st.smTEnd = millis()-1;          // drag end-time to avoid wrap-around errors
  }
  
  if( DIFF(millis(), st.backLightEnd) > 0 ) {
    lcd_light( false );
    st.backLightEnd = millis()-1;   // drag end-time to avoid wrap-around errors
  }

  if( (st.wdKey & WD_KEY_CHECK) == WD_KEY_CHECK ) wdt_reset();
  
}
