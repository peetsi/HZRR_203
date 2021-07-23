
/*
 * same as arduino_EEPROM01 but extended with EEPROM write and read
 * 
 * function:
 * + check if parameter data in EEPROM are valid using checksum; 
 * + if so read from EEPROM to parameter data structure
 * + else use default values and store them 
 *   + to parameter data struct 
 *   + AND to EEPROM including checksum as LAST struct-item
 */

// --------------------------
// INCLUDES
// --------------------------

#include "hr2_regler.h"
#include "hr2_eeprom.h"

// --------------------------
// VARIABLES, GLOBAL
// --------------------------



// --------------------------
// FUNCTIONS for EEPROM
// --------------------------

/* +++ WARNING +++ WARNING +++ WARNING +++
 *  avoid permanent writes to EEPORM; it gets defective 
 *  after about 20,000 writes !!!
 */



// Calculate checksum from a given c-structure
uint32_t checksum_struct( parameter_t *ps ) {
  // ps   p)ointer to s)tructure data; last field contains the uint32_t checksum
  int i;
  int n = sizeof(*ps) - 4;            // without the trailing 4 checksum bytes
  uint8_t *bp = (uint8_t*)ps;       // point to first byte of structure  
  uint32_t checksum = 0;
  for(i=0;i<n;i++) {
    checksum += *bp++;      // take byte-value of address bp and THEN increment address
  }
  return checksum;
}


// Read data from eeprom; 
bool eeprom_get_parameter( uint16_t eeAddress ) {
  // input:   eeAddress      begin of data in eeprom
  //          par (global)   is filled with data from eeprom
  // return:  True if checksum is valid
  uint32_t cs;

  EEPROM.get( eeAddress, par ); // fills parameter structure with eeprom data
  cs = checksum_struct( &par );
  if( cs == par.checksum ) {
    return true;
  }
  else {
    return false;
  }
}


// Write data to eeprom
void eeprom_put_parameter( uint16_t eeAddress ) {
  // input:   eeAddress     begin of data in eeprom
  //          par (global)  data to be written
  par.checksum = checksum_struct( &par );
  EEPROM.put(eeAddress,par);    
  //Serial.println(F("written toEEPROM"));
}


// set all bytes in EEPROM to 0xFF (all bit high <-> emptiy)
// NOTE: takes some time depending on size of EEPROM
void eeprom_clear( void ) {
  for (uint16_t i = 0 ; i < EEPROM.length() ; i++) {
    EEPROM.write(i, 0xFF);   // an empty eeprom has all bits set to 1
  }
   //Serial.println(F("EEPROM cleared"));
}


void init_var_status(void){
  byte i;
  // for the module:
  st.modAddr = get_address();
  st.comefrom = 1;
  st.tNextMeas = 0;
  // error numbers
  st.errCom = 0;
  st.errMod = 0;
  // measured values
  st.cmdAddress = 0;
  st.rTemp  = 0.0;
  st.rMode = 0;
  // temperature Vorlauf from heating central
  st.tempVlRx = 0.0;
  st.tVlRxEnd = millis();

  // rx (received) command variables, received from master
  st.rxCmdNr = 0;
  st.rxBuf[0] = 0;
  st.rxCmdReady = 0;   
  st.rxCmdLen = 0;    
  st.rxTTL = 0;       
  st.rxReg = 0;       
  st.rxAdr = -1;      
//  st.rxSenderAdr = -1;

  // tx (send) Command variables; send to master
  //st.txCmdSend = 0;
  st.txCmdNr = 0;  
  st.txReg = 0;    
  
  // wrapper
  st.modbWrapped[0] = 0;

  // variables for running ONE motor
  //   for tech. reasons only one motor can run at a time; 
  //   the regulator status sets a request for its correlated motor-valve to run in <direction> for <time> msec.
  //   the ISR looks at these data and controls one motor after the other;
  //   following variables are used for this
  st.motRunning = MOT_FREE;
  st.motReady = false;
  st.motDir = MOT_STOP; 
  st.tMotEnd = 0;
  st.tMotDelayEnd = 0;
  st.motUsV = 0.0;
  st.motImA = 0.0;
  //st.motImAOld = 0.0;
  //st.motImALP = 0.0;
  st.motStop = 0;
  //uint32_t motCurrDelay;

  st.but = 0;
  st.butOld = 0;
  st.butPressed = 0;
  st.lcdService = 0;
  st.smm  = 0;
  st.smf  = 0; 
  // for all regulators
  st.tempRlSoll  = 0.0;
  st.tDs18b20End = millis();
  st.iTemp = 0;

  for(i=0;i<3;i++){
    regStatus_t* sr = &st.r[i];
    sr->active = par.r[i].active;
    sr->motConnected = MOT_NOT_TESTED; //
    sr->motStart = 0;
    sr->motReady = true;
    sr->motDir   = MOT_STOP;
    sr->tMotDur  = 0;
    sr->motPos   = 0;
    // valve-motor status
    //sr->motLimit = MOT_STOP;
    // regulator variables  
    sr->firstLoop = true;
    sr->tempVlMeas = 70.0;
    sr->tempVl     = 70.0;
    sr->tempVlLP1  = 70.0;
    sr->tempRlMeas = 40.0;
    sr->tempRlLP1 = 40.0;
    sr->tempRlLP2 = 40.0;
    sr->mRl = 0.0;
    sr->mPauseEnd = millis();
    sr->mPause = false;
    sr->motBoostEnd = millis();
    sr->motBoost = false;
    sr->motGotoStart = 0;
    sr->motCalib = 0;
  }
}


void init_var_position( byte mode ) {
  // mode   0  after reset or power up
  //        1  while running, e.g. lcd change
  byte i;

  for(i=0;i<3;i++){
    if( mode == 0 ) {
      st.r[i].motLimit = MOT_STOP;        // MOT_STOP, exact position unknown
      st.r[i].motPos = 0.0;
    }
    else {
      if( st.r[i].motLimit == MOT_STOP ){
        // do nothing
      }
      else if( st.r[i].motLimit == MOT_CLOSE ){
        st.r[i].motPos = 0.0;
      }
      else if( st.r[i].motLimit == MOT_OPEN ){
        st.r[i].motPos = 999.0;
      }
      else if( st.r[i].motLimit == MOT_STARTPOS ){
        if( par.r[i].dtOpen == 0 ) { par.r[i].dtOpen = 30;}  // use typical value to avoid div-0
        st.r[i].motPos = (999.0 * (float)par.r[i].dtOffset / ((float)par.r[i].dtOpen)*1000.0);
      }
      else {
        st.r[i].motPos = 500.0;   // try some middle position
      }
    }
  }
}


void init_var_parameter(void){
  byte i;

// for the module:
  par.timer1Tic        = 10;      // ms;    Timer1 period
  par.tMeas            =120;      // sec;   measuring interval  plpl
  par.dtBackLight      = 10;      // min;  time to keep backlight on
  par.fastMode         = 0;       // normal operation speed
  // common to all regulators
  
  par.tv0             = 40.0;    // degC; characteristic curve
  par.tv1             = 75.0;    // degC;   see function
  par.tr0             = 32.0;    // degC;   characteristic()
  par.tr1             = 46.0;    // degC;   (Kennlinie)
  par.tVlRxValid      = 30;      // min;  use central Vorlauf temperature until this time
  par.tempZiSoll      = 20.0;    // degC; can be varied +/-4K with Zimmer Thermostat
  par.tempZiTol       =  0.5;    // degC; tolerance

  // for each regulator
  for(i=0;i<3;i++){
    par.r[i].active         =      1;     // ;      see below for Zimmertemperatur Regelung
                                          //        reg-1 (index 0): always active unless 0 here
                                          //        reg.2,3 (index 1,2): only active if jumper is set
    // valve motor
    par.r[i].motIMin        =      5;     // mA;    
    par.r[i].motIMax        =     70;     // mA;    
    par.r[i].tMotDelay      =     80;     // ms;    
    par.r[i].tMotMin        =    100;     // ms;    
    par.r[i].tMotMax        =     40;     // sec;    
    // open- and close times for valves       measured        clock     millis()
                                           // ms;   motor     Auf  Zu   Open   Close
                                           //       1 o.Vent. 30.5 30.2 27579  27577
                                           //       1 LinVen. 31   37   27576  33397
                                           //       1 EckVen. 30.4 38.4 27572  34464  
                                           //       2 o.Vent. 32.0 31.7 28632  28637
                                           //       2 LinVen. 31.2 37.9 28108  33934
                                           //       2 EckVen. 31   36   27577  33873
                                           // valves from "THE"
    par.r[i].dtOpen         =     28;     // sec;
    par.r[i].dtClose        =     34;     // sec;   
    par.r[i].dtOffset       =   3000;     // ms;
    par.r[i].dtOpenBit      =    500;     // ms;
    // regulation
    // *** pl: p-factor changed from 0.1 to 0.03 in Version 1.0.3
    par.r[i].pFakt          =      0.03;  // s/K;     dT=3.3K => t=0.1s => 0.1sec motor on time
    par.r[i].iFakt          =      0.0;   // s/(K*s); dT=1K, t= 3h  => ca. 1e-4sec motor on time 
    par.r[i].dFakt          =      0.0;   // s^2/K;   dT=1K, t=50s  => ca. 0.1sec motor on time
    //par.r[i].tauTempVl      = 1.0*60.0;   // sec;   
    //par.r[i].tauTempRl      = 3.0*60.0;   // sec;   
    //par.r[i].tauM           = 2.0*60.0;   // sec;   
    par.r[i].tauTempVl      =        1;   // sec;     if <= par.tMeas: faktor=1; Low-pass switched off 
    par.r[i].tauTempRl      =        1;   // sec;   
    par.r[i].tauM           =        1;   // sec;   
    par.r[i].m2hi           =     50.0;   // mK/s;  
    par.r[i].m2lo           =    -50.0;   // mK/s;  
    par.r[i].tMotPause      =10.0*60;     // sec;   
    par.r[i].tMotBoost      =    900;     // sec; 
    par.r[i].dtMotBoost     =   2000;     // ms; 
    par.r[i].dtMotBoostBack =   2000;     // ms; 
    par.r[i].tempTol        =      2.0;   // K;     
    statist.tMotTotal[i]    =      0.0;   // sec;
    statist.nMotLimit[i]    =      0;     // 1;
  }
  statist.nBoot             =      0;
}




// Fill parameter structure from EEPROM 
// if not available: use default values and store them to EEPROM
uint8_t get_parameter( void ) {
  // input:    par (global) to be filled
  uint8_t rv;  // return value
  rv = eeprom_get_parameter( EEPROM_PARAMETER_ADDRESS );
  if( !rv ) {
    //Serial.println(F("EEPROM data wrong"));
    rv=1;
    init_var_parameter();
    eeprom_put_parameter( EEPROM_PARAMETER_ADDRESS );
    //Serial.println(F("write factory setting to EEPROM"));
  }
  else{
    //Serial.println(F("using EEPROM data"));
    rv=0;
  }
  return rv;
}
