
/*
 * hr2_comm.cpp
 * 
 * test functions for software testing
 * 
 */

#include <stdio.h>
#include <stdlib.h>
#include "hr2_comm.h"


// --------------------------
// VARIABLES, GLOBAL
// --------------------------


// ---------------------------------
// FUNCTIONS for RS485 communication
// ---------------------------------
// ATTENTION: Buffersize of Arduino Serial Rx-Tx is 64Bytes each as a standard;
//            communications is kept below this limit;
// buffersize could be changed in file:
// <base Arduino folder>\hardware\arduino\avr\libraries\SoftwareSerial\SoftwareSerial.h
// TODO: add timeout; 
// TODO: reset Serial if it hangs


byte hex2byte( char* s ) {
  // s is a 2 digit hex number (not necessarily 0-terminated) 
  // -> return one binary byte; e.g. string "FE" -> byte 0xFE
  if( !( isxdigit(s[0]) && isxdigit(s[1]) ) ) {
    return 0;
  }
  //            '0' = 0x30 ...
  //            '9' = 0x39
  // upper-case 'A' = 0x41 --- &0x0F -> 0x01
  // lower-case 'a' = 0x61 --- &0x0F -> 0x01
  byte c;
  c = s[0];
  byte hi = (c <= '9') ? c & 0x0F  :  (c & 0x0F) + 9;  
  c = s[1];
  byte lo = (c <= '9') ? c & 0x0F  :  (c & 0x0F) + 9;
  return (hi << 4) + lo;
}


byte rs485_write(void){
  Serial.flush();                     // wait for arduino-tx-buffer beeing empty !!!
  digitalWrite( DE485_PIN, 1 );       // switch RS485 driver to transmit
  delayMicroseconds(100);
  Serial.print(st.txBuf);
  Serial.flush();                     // wait for arduino-tx-buffer beeing empty !!!
  delayMicroseconds(100);
  digitalWrite( DE485_PIN, 0 );       // switch back to read again
  return SER_TX_SENT;
}


void rs485_readln( void ){
  // wait for a ':' to begin with recording of a command line
  // read a whole line until a '\r' '\n' = <cr><lf> is received;
  // make empty string on overflow
  // NOTE: ':' is NOT ALLOWED inside the data packets! assumes new command start
  // NOTE: Serial.flush() does nothing with the input buffer !!!
  // st.rxBuf    received string
  char c;
  while( Serial.available() ) { 
    c = Serial.read();
    // *** wait for leading ':' of a message
    if( (st.rxCmdLen==0)&&(c!=':')) {
      return;
    }
    if( c == ':' ) {
      st.rxBuf[0] = c;            // read next character
      st.rxBuf[1] = 0;            // terminate string
      st.rxCmdLen=1;              // will be string length
    }
    else if( (c == '\r')||( c == '\n') ){
      // *** end of command reached
      st.rxBuf[st.rxCmdLen] = 0;
      st.rxCmdReady = 1;        // command received
    }
    else {
      // *** add c to string
      st.rxBuf[st.rxCmdLen] = c;    // read next character
      st.rxCmdLen++;                // will be string length
      st.rxBuf[st.rxCmdLen] = 0;    // terminate string
    }
    if( st.rxCmdLen >= STR_RX_MAXLEN-2 ){
      // discard received data    // do not use '.flush()' - waits for tx ready
      //SPRL(F("rs485_readln: OVERFLOW rxCmdLen="),st.rxCmdLen);
      st.rxCmdReady = 0;          // command ignored
      st.rxCmdLen=0;              // reset count
      st.rxCmdReady = 0;          // no receiving cmd in progress
      st.rxBuf[0] = 0;            // set rx-buffer to empty string
      return;
    }
  }
}
  


// ----------------------------
// *** modbus
// ----------------------------

void modbus_header( void ) {
  // generate leading part of tx string; target address is 00
  // ":0001020b" without payload string, checksum, LRC and cr-lf at the end
  sprintf( st.txBuf, ":00%02X%02X%d%c", st.txCmdNr, st.modAddr, st.txReg, PROT_REV );
  // ":0001020bACK008E03"
}


byte modbus_trailer( void ) {
  // st.txBuf    string to be completed 
  // generates answer string to command, e.g. 1 at module addr. 2:
  // ":0001020bACK008E03"
  // :     lead-in
  // 00    master-address of packet (central PC)
  // 01    command nr to which was answered
  // 02    from-address (own module address)
  // 0     sub-address, 0=module, 1,2,3 is regulator 0,1,2
  // b     protocol type b for HZRR200
  // ACK   payload string
  // 008E  checksum
  // 03    LRC
  // \r\n  cr-lf at end of line
  char hs[10];
  byte ls = strlen(st.txBuf); // Länge LRC Berechnung
  //SPR(F("wrap: ls="),ls); Serial.println(st.txBuf);
  if(ls > STR_TX_MAXLEN - 7) {
    st.msg |= MSG_COM_TX_OVF;
    return MSG_COM_TX_OVF;
  }

  // *** calculate checksum and add it to string
  uint16_t ccs = 0;
  for(byte i=1;i<ls;i++){
    ccs +=st.txBuf[i];
  }
  sprintf(hs,"%04X",ccs);
  strcat(st.txBuf,hs);
  ls += 4;
  
  // *** calculate lrc (xor bitwise all bytes after ':' to the end)
  byte lrc = 0;
  for (int i=1; i<ls; i++) {lrc = lrc ^ st.txBuf[i];}
  sprintf(hs,"%02X\r\n", lrc);
  strcat(st.txBuf, hs);
  //SPRL(F("trailer: send "),st.txBuf);
  rs485_write();
  st.txBuf[0]=0;
  return MB_WRAP_READY;
}

  
byte modbus_unwrap(void) {
  // return      in st.rxCmd
  // *** unwrap incoming data packet
  // *** check for Address, protocol version, LRC and checksum and form
  //     set st.rxAdr, st.rxReg and  st.rxReg 
  // example: command nr. 1 'ping':
  //     ":02010b015550\r\n\0" 
  //     ':'     lead in
  //     "02"    module-address 2, 
  //     "01"    command Nr 1  (ping)
  //     '0'     sub-address of regulator: module itself, 
  //     'b'     protocol version b,
  //     ""      no payload string
  //     "0155"  checksum string
  //     "50"    LRC
  //     "\r\n"  cr-lf end of packet
  //     '\0'    string termination
  char* s = st.rxBuf;     // string to be unwrapped
  
  if( !( s[0]==':' && isxdigit(s[1]) && isxdigit(s[2]) ) ) {
    // no message
    return MB_ADR_WRONG;            // discard if wrong format
  }

  // *** read module-address
  st.rxAdr = hex2byte(&s[1]);       // converts two chars
  if( st.rxAdr != st.modAddr ) {
    // no message - normal used for other module
    return MB_ADR_WRONG;            // discard if not own address
  }

  // *** read command nr.
  st.rxCmdNr = hex2byte(&st.rxBuf[3]);

  // *** regulator/module address
  //     should be in range 0...3
  byte r = s[5] - '0';
  if(r > 3){

    return MB_ADR_WRONG;            // discard if wrong reg/mod address
  }
  st.rxReg = r;

  if( s[6] != PROT_REV ) {
    st.r[r].msg |= MSG_COM_RX_WPROT;
    return MB_ADR_WRONG;            // discard if wrong protocol version
  }

  // *** check LRC
  // ping cmd 1 for addr. 2 is: ":02010b00F346"; trailing "\r\n" is not stored
  byte ls = strlen(s);
  // byte rlrc = (byte)strtoul(&s[ls-2],NULL,16);  // consumes 510 bytes !!!
  byte rlrc = hex2byte( &s[ls-2] );   // received LRC
  byte clrc = 0;                      // calculated LRC
  for(byte i=1;i<ls-2;i++){
    clrc ^= s[i];
  }
  if( clrc ^ rlrc ){
    st.r[r].msg |= MSG_COM_RX_WLRC;
    return MB_ADR_WRONG;            // discard if wrong LRC
  }

  // *** checksum
  uint16_t a = hex2byte(&s[ls-6]);
  uint16_t b = hex2byte(&s[ls-4]);
  
  uint16_t rcs = (a<<8) + b;
  uint16_t ccs = 0;
  for(byte i=1;i<ls-6;i++){
    ccs += s[i];
  }
  if( ccs - rcs ){
    st.r[r].msg |= MSG_COM_RX_WCS;
    return MB_ADR_WRONG;            // discard if wrong checksum
  }
  
  return MB_ADR_OK;    
}


void send_ack(void){
  modbus_header();
  strcat(st.txBuf,",ACK,");
  modbus_trailer();
}


void send_nak(void){
  modbus_header();
  strcat(st.txBuf,",NAK,");
  modbus_trailer();
}


char* find_next_char( char* cp, char c ) {
  while( *cp && (*cp++ != c));
  return cp;
}


void show_param(byte mode) {
  // mode   bitflags: 0x01:module; 0x02:reg1; 0x04:reg2; 0x08:reg3
  //return;   // for debug: uncomment
  // module
  // cmd 0x22 module
  //SPRL(F("param, mode="),mode);
  if(mode & 0x01){
    //SPRL(F(" timer1Tic="),par.timer1Tic);
    //SPRL(F(" tMeas="),par.tMeas);
    //SPRL(F(" dtBackLight="),par.dtBackLight);
    //SPRL(F(" tv0="),par.tv0);
    //SPRL(F(" tv1="),par.tv1);
    //SPRL(F(" tr0="),par.tr0);
    //SPRL(F(" tr1="),par.tr1);
    //SPRL(F(" tVlRxValid="),par.tVlRxValid);
    //SPRL(F(" tempZiTol="),par.tempZiTol  );
    //SPRL(F(" tVlRxValid="),par.tVlRxValid);
    //Serial.println();
  }
  // regulators
  for(int ri=0;ri<3;ri++) {
    if( mode & (1<<(ri+1))){
      regParam_t* p = &par.r[ri];
      // cmd 0x22 regulator
      //SPRL(F("parse 0x22: ri="),ri);
      //SPRL(F(" active="),p->active);
      //SPRL(F(" motIMin="),p->motIMin);
      //SPRL(F(" motIMax="),p->motIMax);
      //SPRL(F(" tMotDelay="),p->tMotDelay);
      //SPRL(F(" tMotMin="),p->tMotMin);
      //SPRL(F(" tMotMax="),p->tMotMax);
      //SPRL(F(" dtOpen="),p->dtOpen);
      //SPRL(F(" dtClose="),p->dtClose);
      //SPRL(F(" dtOffset="),p->dtOffset);
      //SPRL(F(" dtOpenBit="),p->dtOpenBit);
      // cmd 0x23 regulator
      //SPRL(F("parse 0x23: ri="),ri);
      //SPRL(F(" pFakt="),p->pFakt);
      //SPRL(F(" iFakt="),p->iFakt);
      //SPRL(F(" dFakt="),p->dFakt);
      //SPRL(F(" tauTempVl="),p->tauTempVl);
      //SPRL(F(" tauTempRl="),p->tauTempRl);
      //SPRL(F(" tauM="),p->tauM);
      // cmd 0x24 regulator
      //SPRL(F("parse 0x24: ri="),ri);
      //SPRL(F(" m2hi="),p->m2hi);
      //SPRL(F(" m2lo="),p->m2lo);
      //SPRL(F(" tMotPause="),p->tMotPause);
      //SPRL(F(" tMotBoost="),p->tMotBoost);
      //SPRL(F(" dtMotBoost="),p->dtMotBoost);
      //SPRL(F(" dtMotBoostBack="),p->dtMotBoostBack);
      //SPRL(F(" tempTol="),p->tempTol);
      //Serial.println();
    }
  }
  //Serial.println();
}


void parse_cmd(void) {
  // *** read command nr and perform related action
  //     blocks st.rxBuf till command is completed
  //     blocks st.txBuf till answer ist sent
  byte ri;                  // regulator index = regulator Nr. - 1 e [0,1,2]
  
  char* s1 = st.txBuf;
  char* sp = find_next_char(st.rxBuf,','); // unwrapped commandstring ("payload")
  byte  sl = strlen(st.rxBuf);
  st.rxBuf[sl-7]=0;                        // strip off checksum etc.
  //SPRL(F(" sp="),sp);
  
  char *cp = sp;    // cp iterates through the command 
  char *cp0;        // dummy, not further used
  char hs[30];      // help string as short buffer

  //Serial.print(F("parse: ")); freemem();
  
  // *** read command nr
  //SPRL(F(" st.rxCmdNr="),st.rxCmdNr );

  st.txCmdNr = st.rxCmdNr;
  st.txReg   = st.rxReg;    // e [0,1,2,3] for [module,reg1,reg2,reg3]

  // NOTE: do not deny inactive regulators: active may change !!!

  ri = st.rxReg-1;         // regulator index e [0,1,2]

  //SPRL(" st.txReg=",st.txReg);
  if( st.txReg > 3 ) {     // unsigned; no negaive numbers
    send_nak(); 
    return;
  }

  parameter_t* mp_p;    // module parameter-pointer
  mp_p   = &par;  
  regParam_t* rp_p;     // regulator pararameter-pointer
  rp_p  = &par.r[ri];
  status_t* st_p;       // status value pointer
  st_p = &st;
  regStatus_t* rst_p;    // regulator status value pointer
  rst_p = &st.r[ri];     

  switch( st.rxCmdNr ) {
    case 1:
      // response to ping-command
      st.txReg = 0;
      send_ack();
    break;

    case 2:   // send status data
      // *** requested data for compatibility with previous version of system hz-rr010
      //     =========================================================================
      // originally stored log-data from hzrr-010 project log-file:
      //     "20191018_020336 0201 HK2 :0002021a t117073.6  S VM 39.0 RM 37.7 VE 20.0 RE 37.7 RS 32.3 P073 E0000 FX0 M5406 A0"
      // containing:
      //   header from python log-script:
      //     20191018_020336  date-time
      //     0201             command+module
      //     HK2              Heizkreis+Nr
      //        
      //   data from version 010 modules:
      //     ":0002021a t117073.6  S VM 39.0 RM 37.7 VE 20.0 RE 37.7 RS 32.3 P073 E0000 FX0 M5406 A0"
      //     with:
      //       :
      //       0002021a   00:master addr. 02:command nr. 02:from module nr. 1:reg.nr a:protocol version
      //       t117073.6  internal timer tic in seconds
      //       S          S:summer W:winter operation
      //       VM 39.0    Vorlauf temperature measured locally / -9.9 if roomtemperature reg.
      //       RM 37.7    Ruecklauf temperature measured / Roomtemperature if reg.2 and roomtemp
      //       VE 20.0    Volauf temperature effectively used
      //       RE 37.7    Ruecklauf temperature effectively used
      //       RS 32.3    Ruecklauf temperature set value (Sollwert) 
      //       P073       Percent 0..100 of relative valve position
      //       E0000      Error / Message flags
      //       FX0        a fixed position is reached, i.e. open, close, startpos or not defined
      //       M5406      total motor-on time
      //       A0         number of limits reached
      //
      // *** data will be fetched from module with commands Nr. 2 and 4
      //
      if( st.rxReg == 0 ) {
        // module status
        send_ack();
      }
      else {
        // controller status
        // *** build line of measured values
        // no winter- or summer operation -> omitted in type b protocol
        // cmd = 2
        // VM RM: Vl/Rl temp. measured
        // VE RE: Vl/Rl temp. effectively used for regulation
        // RS:    Rl temp. soll
        // PM:     Permille motor-valve setting; 0=closed, 999=open
        // cmd = 4
        // ER:     Error message bits set
        // FX:    fixed position; MOT_STOP (somewhere), MOT_STARTPOS, MOT_CLOSE or MOT_OPEN
        // MT:     total motor-on time
        // NL:     Number of limits reached (higher load to gears)
        //           1         2         3         4         5         6  
        //  1234567890123456789012345678901234567890123456789012345678901234
        // ":00021E1b,W,VM0.0,RM0.0,VE0.0,RE0.0,RS0.0,PM0,09AB01cl0"  // could become a bit longer; OK
        //  rest ---> moved to command 4
        
        modbus_header();
        //SPRL(F("hs="),hs);
        strcat(s1,","); hs[0]=st.r[ri].season; hs[1]=0;      strcat(s1,hs);
        if( (ri==1) and (st.roomReg > 0) ){
          rst_p->tempVlMeas = -9.9;    // indicate room-temperature regulator
          rst_p->tempRlMeas = st.rTemp;
          rst_p->tempVl     = -9.9;
          rst_p->tempRlLP2  = st.rTemp;
        }
        strcat(s1,",VM"); dtostrf(rst_p->tempVlMeas,3,1,hs); strcat(s1,hs);
        strcat(s1,",RM"); dtostrf(rst_p->tempRlMeas,3,1,hs); strcat(s1,hs);
        strcat(s1,",VE"); dtostrf(rst_p->tempVl,3,1,hs);     strcat(s1,hs);
        strcat(s1,",RE"); dtostrf(rst_p->tempRlLP2,3,1,hs);  strcat(s1,hs);
        strcat(s1,",RS"); dtostrf(rst_p->tempSoll,3,1,hs);   strcat(s1,hs);
        strcat(s1,",PM"); dtostrf(rst_p->motPos,1,0,hs);     strcat(s1,hs);
        strcat(s1,",");
        modbus_trailer();
        /*
        //SPR(" VM",hs);SPRL(" tempVlMeas=",rst_p->tempVlMeas);
        //SPR(" RM",hs);SPRL(" tempRlMeas=",rst_p->tempRlMeas);
        //SPR(" VE",hs);SPRL(" tempVl=",rst_p->tempVl);
        //SPR(" RE",hs);SPRL(" tempRlLP2=",rst_p->tempRlLP2);
        //SPR(" RS",hs);SPRL(" tempSoll=",rst_p->tempSoll);
        //SPR(" PM",hs);SPRL(" motPos=",rst_p->motPos);
        //SPRL(F(" s1="),st.txBuf); 
        */
      }
    break;

    //case 3:   // not implemented; used in hr010; leave commented out for "NAK" answer
    //break;

    case 4:     // send second part of status information (was in fnc1 in hr010)
      if( st.rxReg == 0 ) {
        // module status
        send_ack();
      }
      else {
        //           1         2         3         4         5         6   
        //  1234567890123456789012345678901234567890123456789012345678901234
        // ":0004021b,ER111111,FX22,MT33333.33,NL44444,NB55555,06BA28cl0"
        modbus_header();
        strcat(s1,",ER");  ltoa(rst_p->msg,hs,16);          strcat(s1,hs);
        strcat(s1,",FX");  itoa(rst_p->motLimit,hs,10);     strcat(s1,hs);
        strcat(s1,",MT");  dtostrf(statist.tMotTotal[ri],1,0,hs); strcat(s1,hs);
        strcat(s1,",NL");  itoa(statist.nMotLimit[ri],hs,10);     strcat(s1,hs);
        strcat(s1,",NB");  itoa(statist.nBoot,hs,10);             strcat(s1,hs);
        strcat(s1,",");
        modbus_trailer();
        /*
        //SPR(" ER",hs);SPRL(" msg=",rst_p->msg);
        //SPR(" FX",hs);SPRL(" motLimit=",rst_p->motLimit);
        //SPR(" MT",hs);SPRL(" tMotTotal=",statist[ri].tMotTotal);
        //SPR(" NL",hs);SPRL(" nMotLimit=",statist[ri].nMotLimit);
        //SPR(" NB",hs);SPRL(" nBoot=",statist.nBoot);
        //SPRL(F(" s1="),st.txBuf); 
        */
      }
    break;

    case 5:     // send parameter
      modbus_header();
      if( st.rxReg == 0 ) {   // send parameter for module
        // typical command: ":02050b015958"
        //           1         2         3         4         5         6   
        //  1234567890123456789012345678901234567890123456789012345678901234
        // ":0005020b,10,30,10,40.0,75.0,32.0,46.0,15,20.0,0.5,09924E\r\n"
        strcat(s1,","); itoa(mp_p->timer1Tic,hs,10);      strcat(s1,hs);
        strcat(s1,","); itoa(mp_p->tMeas,hs,10);          strcat(s1,hs);
        strcat(s1,","); itoa(mp_p->dtBackLight,hs,10);    strcat(s1,hs);
        strcat(s1,","); dtostrf(mp_p->tv0,1,1,hs);        strcat(s1,hs);
        strcat(s1,","); dtostrf(mp_p->tv1,1,1,hs);        strcat(s1,hs);
        strcat(s1,","); dtostrf(mp_p->tr0,1,1,hs);        strcat(s1,hs);
        strcat(s1,","); dtostrf(mp_p->tr1,1,1,hs);        strcat(s1,hs);
        strcat(s1,","); itoa(mp_p->tVlRxValid,hs,10);     strcat(s1,hs); 
        strcat(s1,","); dtostrf(mp_p->tempZiSoll,1,1,hs); strcat(s1,hs); 
        strcat(s1,","); dtostrf(mp_p->tempZiTol  ,1,1,hs);strcat(s1,hs);
        strcat(s1,",");
      }
      else{                   // send parameter for regulator, part 1
        // typical command: ":02060b015958"
        //           1         2         3         4         5         6   
        //  1234567890123456789012345678901234567890123456789012345678901234
        // ":00051E1b,1,222,333,444,555,666,777,7888,9999,074415cl0"
        // ":00051E1b,1,5,70,80,100,40,28,34,3000,074415cl0"
        strcat(s1,","); itoa(rp_p->active,hs,10);       strcat(s1,hs);  //   1 |  1    uint8_t
        strcat(s1,","); itoa(rp_p->motIMin,hs,10);      strcat(s1,hs);  // 222 |  mA   int16_t
        strcat(s1,","); itoa(rp_p->motIMax,hs,10);      strcat(s1,hs);  // 333 |  mA   int16_t
        strcat(s1,","); itoa(rp_p->tMotDelay,hs,10);    strcat(s1,hs);  // 444 |  ms   int16_t
        strcat(s1,","); itoa(rp_p->tMotMin,hs,10);      strcat(s1,hs);  // 555 |  ms   uint16_t
        strcat(s1,","); itoa(rp_p->tMotMax,hs,10);      strcat(s1,hs);  // 666 |  sec  uint8_t
        strcat(s1,","); itoa(rp_p->dtOpen,hs,10);       strcat(s1,hs);  // 777 |  sec  uint8_t
        strcat(s1,","); itoa(rp_p->dtClose,hs,10);      strcat(s1,hs);  // 888 |  sec  uint8_t
        strcat(s1,","); itoa(rp_p->dtOffset,hs,10);     strcat(s1,hs);  //9999 |  ms   uint16_t
        strcat(s1,","); itoa(rp_p->dtOpenBit,hs,10);    strcat(s1,hs);  //9999 |  ms   uint16_t
        strcat(s1,",");
      }
      modbus_trailer();
    break;
    
    case 6:     // send parameter
      if( st.rxReg == 0 ) { // send no parameter for module (was sent fully in cmd 5)
        send_ack();
      }
      else{  // send parameter for regulator, part 2
        // typical command: ":02060b015958"
        //           1         2         3         4         5         6   
        //  1234567890123456789012345678901234567890123456789012345678901234
        // ":0005020b,1.111,2.222,3.333,444.44,555.55,666.66,09924E\r\n"
        // ":00061E1b,0.100,0.000,-0.002,600.00,1800.00,120.00,09F64B\r\n"

        //
        modbus_header();
        strcat(s1,","); dtostrf(rp_p->pFakt,5,3,hs);    strcat(s1,hs);  // 1.111    |  s/K  float
        strcat(s1,","); dtostrf(rp_p->iFakt,5,3,hs);    strcat(s1,hs);  // 2.222    |  1/K  float
        strcat(s1,","); dtostrf(rp_p->dFakt,5,3,hs);    strcat(s1,hs);  // 3.333    |  s2/K float
        strcat(s1,","); dtostrf(rp_p->tauTempVl,4,2,hs);strcat(s1,hs);  // 444.44   |  1/s  float
        strcat(s1,","); dtostrf(rp_p->tauTempRl,4,2,hs);strcat(s1,hs);  // 555.55   |  1/s  float
        strcat(s1,","); dtostrf(rp_p->tauM,4,2,hs);     strcat(s1,hs);  // 666.66   |  1/s  float
        strcat(s1,",");
        modbus_trailer();
      }
    break;

    case 7:     // send parameter
      if( st.rxReg == 0 ) { // send no parameter for module (was sent fully in cmd 5)
        send_ack();
      }
      else{  // send parameter for regulator, part 3
        // typical command: ":02060b015958"
        //           1         2         3         4         5         6   
        //  1234567890123456789012345678901234567890123456789012345678901234
        // ":0005020b,1.111,2.222,3333,4444,5555,6666,7.7,09924E\r\n"
        //
        modbus_header();
        strcat(s1,","); dtostrf(rp_p->m2hi,5,3,hs);       strcat(s1,hs);  // 1.111    |  K/s  float
        strcat(s1,","); dtostrf(rp_p->m2lo,5,3,hs);       strcat(s1,hs);  // 2.222    |  K/s  float
        strcat(s1,","); itoa(rp_p->tMotPause,hs,10);      strcat(s1,hs);  // 3333     |  sec  uint8_t
        strcat(s1,","); itoa(rp_p->tMotBoost,hs,10);      strcat(s1,hs);  // 4444     |  sec  uint8_t
        strcat(s1,","); itoa(rp_p->dtMotBoost,hs,10);     strcat(s1,hs);  // 5555     |  ms   uint8_t
        strcat(s1,","); itoa(rp_p->dtMotBoostBack,hs,10); strcat(s1,hs);  // 6666     |  ms   uint8_t
        strcat(s1,","); dtostrf(rp_p->tempTol,5,3,hs);    strcat(s1,hs);  // 7.7      |  K    float
        strcat(s1,",");
        modbus_trailer();
      }
    break;

    case 0x20:  // set Vorlauf temperature from Zentrale
      // received command is ":02200b,45.6,02634C" for address 2 and 45.6 degC
      st.tempVlRx = strtod( sp, &cp0 );
      st.tVlRxEnd = millis() + (uint32_t)mp_p->tVlRxValid * 60000L;
      send_ack();
      //SPRL(F(" cmd0x20: tempVlRx="),st.tempVlRx);
    break;

    // *** parameters
    /*
    // for the module:
      uint16_t timer1Tic;              // ms;    Interrupt heartbeat of Timer1     
      uint16_t tMeas;                  // sec;   measuring interval
      uint8_t dtBackLight;             // min;   LCD time to switch off backlight
    
      // common to all regulators
      // characteristic curve (Kennlinie)
      float    tv0,tv1,tr0,tr1;        // degC;  see function characteristic()
      uint8_t tVlRxValid;             // min;    st.tempVlRx is valid this time;
      // regulator 2, regulator-index 1: special Zimmer temperature if mp_p->roomReg != 0:
      float    tempZiSoll;             // degC;  Zimmer temp. soll; +/-4K with room Thermostat
      float    tempZiTol  ;            // degC;  toleracne for room-temperature
    */
    
    //case 0x21:   // not implemented; used in hr010; leave commented out for "NAK" answer
    //break;
    
    case 0x22:     // receive parameters for modules and regulators part 1
      if( st.rxReg == 0 ) {
        //           1         2         3         4         5         6  
        //  1234567890123456789012345678901234567890123456789012345678901234  max. length
        // ":1E220b,010,060,10,40.0,75.0,32.0,46.0,15,20.0,0.5,09A84A"
        // with:        typ.value   use    
        //   :02200b    header;     placeholder
        //   111        10 ms;      timer1Tic; 
        //   222        60 sec;     tMeas; measruring interval
        //   33         10 min;     dtBackLight; time for backlight on after keypressed
        //   44.4       degC;       tv0;   Kurve
        //   55.5       degC;       tv1
        //   66.6       degC;       tr0
        //   77.7       degC;       tr1
        //   88         15 min;     tVlRxValid  
        //   99.9       20 degC;    tempZiSoll
        //   0.5        0.5 degC;   tempZiTol  
        //   02634Ccl0  trailer - placeholder; cl==<cr><lf>0 (end of line)
        
        //SPRL(F("parse 0x22: rxBuf="),st.rxBuf);
        mp_p->timer1Tic = (uint16_t)strtol( cp, &cp0, 10 );
        cp=find_next_char( cp,',');
        mp_p->tMeas = (uint16_t)strtol( cp, &cp0, 10 );
        cp=find_next_char( cp,',');
        mp_p->dtBackLight = (uint8_t)strtol( cp, &cp0, 10 );
        cp=find_next_char( cp,',');
        mp_p->tv0 = (float)strtod( cp, &cp0 );
        cp=find_next_char( cp,',');
        mp_p->tv1 = (float)strtod( cp, &cp0 );
        cp=find_next_char( cp,',');
        mp_p->tr0 = (float)strtod( cp, &cp0 );
        cp=find_next_char( cp,',');
        mp_p->tr1 = (float)strtod( cp, &cp0 );
        cp=find_next_char( cp,',');
        mp_p->tVlRxValid = (uint8_t)strtol( cp, &cp0, 10 );
        cp=find_next_char( cp,',');
        mp_p->tVlRxValid = (uint8_t)strtol( cp, &cp0, 10 );  // ATTENTION: DELETE IN NEW VERSION
        cp=find_next_char( cp,',');
        mp_p->tempZiSoll = (float)strtod( cp, &cp0 );
        cp=find_next_char( cp,',');
        mp_p->tempZiTol   = (float)strtod( cp, &cp0 );
        send_ack(); 
        //SPRL(F(""),);
      }
      else {
        //           1         2         3         4         5         6  
        //  1234567890123456789012345678901234567890123456789012345678901234  max. length
        // ":1E221b,1,5,70,80,100,40,28000,34000,3000,08031C"
        // ":1E221b,1,222,333,444,555,666,777,888,9999,AAAA,08031Ccl0"
        /*
        uint8_t  active;        // 1           0=inactive;
        // valve motor
        int16_t  motIMin;       // 222  mA;    above: normal operation; below: open circuit 
        int16_t  motIMax;       // 333  mA;    above: mechanical limit; 2x: short circuit
        int16_t  tMotDelay;     // 444  ms;    motor current measure delay; (peak current)
        uint16_t tMotMin;       // 555  ms;    minimum motor-on time; shorter does not move
        uint8_t  tMotMax;       // 666  sec;   timeout to reach limit; stop if longer
        uint8_t  dtOpen;        // 777  sec;   time from limit close to limit open
        uint8_t  dtClose;       // 888  sec;   time from limit open to limit close
        uint16_t dtOffset;      // 9999 ms;    time to open valve a bit when close-limit reached
        uint16_t dtOpenBit;     // AAAA ms;    time to open valve a bit if closed is reached

        // parameters received in cmd 0x25
        float    tMotTotal;     // sec;   total motor-on time 
        uint16_t nMotLimit;     // 1;     count of limit-drives of motor 
    
       */
        byte bact= *cp - '0';  // '0';
        //SPRL(" bact=",bact);
        //SPRL(" *cp=",*cp);
        rp_p->active = bact;

        cp=find_next_char( cp,',');
        rp_p->motIMin = (int16_t)strtol( cp, &cp0, 10 );
        cp=find_next_char( cp,',');
        rp_p->motIMax = (int16_t)strtol( cp, &cp0, 10 );
        cp=find_next_char( cp,',');
        rp_p->tMotDelay = (int16_t)strtol( cp, &cp0, 10 );
        cp=find_next_char( cp,',');
        rp_p->tMotMin = (uint16_t)strtol( cp, &cp0, 10 );
        cp=find_next_char( cp,',');
        rp_p->tMotMax = (uint8_t)strtol( cp, &cp0, 10 );
        cp=find_next_char( cp,',');
        rp_p->dtOpen = (uint8_t)strtol( cp, &cp0, 10 );
        cp=find_next_char( cp,',');
        rp_p->dtClose = (uint8_t)strtol( cp, &cp0, 10 );
        cp=find_next_char( cp,',');
        rp_p->dtOffset = (uint16_t)strtol( cp, &cp0, 10 );
        rp_p->dtOpenBit = (uint16_t)strtol( cp, &cp0, 10 );
        send_ack();
        //SPRL(F(""),);
      }
    break;

    case 0x23: // receive parameters for regulators, part 2
      if( st.rxReg == 0 ) {
        send_ack();
      }
      else {         
        //":1E231b,0.100,0.000,0.000,600.00,180.00,120.00,08D942"
        /*
        // regulation
        float    pFakt;         // s/K;   P-factor; motor-on time per Kelvin diff.
        float    iFakt;         // 1/K;   I-factor;
        float    dFakt;         // s2/K;  D-factor; 
        float    tauTempVl;     // sec;   tau; reach 1/e; low-pass (LP) filter Vorlauf
        float    tauTempRl;     // sec;   tau; reach 1/e; LP filter Ruecklauf (RL)
        float    tauM;          // sec;   tau; reach 1/e; LP filter slope m
         */
        rp_p->pFakt = (float)strtod( cp, &cp0 );
        cp=find_next_char( cp,',');
        rp_p->iFakt = (float)strtod( cp, &cp0 );
        cp=find_next_char( cp,',');
        rp_p->dFakt = (float)strtod( cp, &cp0 );
        cp=find_next_char( cp,',');
        rp_p->tauTempVl = (float)strtod( cp, &cp0 );
        cp=find_next_char( cp,',');
        rp_p->tauTempRl = (float)strtod( cp, &cp0 );
        cp=find_next_char( cp,',');
        rp_p->tauM = (float)strtod( cp, &cp0 );
        send_ack();
        //SPRL(F(""),);
      }
    break;

    case 0x24: // receive parameters for regulators, part 3
      if( st.rxReg == 0 ) {
        send_ack();
      }
      else {   
        //":1E241b,50.000,-50.000,600,900,2000,2000,2.0,08852A"
        /*
        float    m2hi;          // K/s;   up-slope; stop motor if above for some time 
        float    m2lo;          // K/s;   down-slope; open valve a bit
        uint16_t tMotPause;     // sec;   time to stop motor after m2hi
        uint16_t tMotBoost;     // sec;   time to keep motor open after m2lo increase flow
        uint16_t dtMotBoost;    // ms;    motor-on time to open motor-valve for boost
        uint16_t dtMotBoostBack;// ms;    motor-on time to close motor-valve after boost
        float    tempTol;       // K;     temperature tolerance allowed for Ruecklauf
         */
        rp_p->m2hi = (float)strtod( cp, &cp0 );
        cp=find_next_char( cp,',');
        rp_p->m2lo = (float)strtod( cp, &cp0 );
        cp=find_next_char( cp,',');
        rp_p->tMotPause = (uint16_t)strtol( cp, &cp0, 10 );
        cp=find_next_char( cp,',');
        rp_p->tMotBoost = (uint16_t)strtol( cp, &cp0, 10 );
        cp=find_next_char( cp,',');
        rp_p->dtMotBoost = (uint16_t)strtol( cp, &cp0, 10 );
        cp=find_next_char( cp,',');
        rp_p->dtMotBoostBack = (uint16_t)strtol( cp, &cp0, 10 );
        cp=find_next_char( cp,',');
        rp_p->tempTol = (float)strtod( cp, &cp0 );
        send_ack();  
        //SPRL(F(""),);
      }
    break;


    case 0x25:  // receive special parameters in regulators 1-3
      if( st.rxReg == 0 ) {
        send_ack();
      }
      else {  
        /*
        float    tMotTotal;     // sec;   total motor-on time 
        uint16_t nMotLimit;     // 1;     count of limit-drives of motor
        */
        statist.tMotTotal[ri] = (float)strtod( cp, &cp0 );
        cp=find_next_char( cp,',');
        statist.nMotLimit[ri] = (uint16_t)strtol( cp, &cp0, 10 );
        send_ack();
        //SPRL(F("tMotTotal="),rp_p->tMotTotal);
        //SPRL(F("nMotLimit="),rp_p->nMotLimit);
        send_ack();
        //SPRL(F(""),);
      } 
    break;

    case 0x30:  // reset all parameters to factory settings
      init_var_parameter();
      send_ack();
      //SPRL(F(" cmd0x30 par factory set"),"");
      show_param(1);
    break;

    case 0x31:  // move valve; time and direction
      if( (st.rxReg==0)||(st.rxReg > 3) ) break;
      //SPRL(F(" cmd0x31: rxBuf="),st.rxBuf);
      uint32_t dt;
      uint8_t  dir;
      dt = (uint32_t)strtol( cp, &cp0, 10 );  // ms;    motor-on time
      cp=find_next_char( cp,',');
      dir= (uint8_t)strtol( cp, &cp0, 10 );  // 1;     direction: 0:close, 1:open, 2:startpos.
      //Serial.print(F("0x31: ri="));Serial.print(ri);
      //Serial.print(F(" dt="));Serial.print(dt);
      //Serial.print(F(" dir="));Serial.print(dir);
      //Serial.println();
      //SPRL(F(" cmd0x31 move valve dt ="),dt);
      //SPRL(F(" cmd0x31 move valve dir="),dir);
      if(dir==0)      {
        valve_action( ri, MOT_CLOSE, dt, false);
      }
      else if(dir==1) {
        valve_action( ri, MOT_OPEN, dt, false);
      }
      else if(dir==2) {
        valve_action( ri, MOT_STARTPOS, dt, false); 
        //SPRL(F(" cmd0x31 startpos "),"");
      }
      send_ack();
    break;

    /*
    case 0x32:  // 
      send_ack();
      //SPRL(F(""),);
    break;

    case 0x33:  // 
      send_ack();
      //SPRL(F(""),);
    break;
    */
    
    case 0x34:  // set valve back to normal control / stop service mode / stop motors
      valve_motor_off_all();
      for( int mot=0;mot<3;mot++){
        motor_off( ri );
      }
      st_p->lcdService = 0;
      st_p->tMotDelayEnd = millis();
      st_p->tMotEnd      = millis();
      st_p->motReady     = true;
      st_p->motRunning   = MOT_FREE;
      st_p->motStop      = 0;             // make sure this flag is zero
      send_ack();
      //SPRL(F("set normal operation"),"");
    break;
    
    case 0x35:  // set regulator to active / inactive
      if(*cp == '0'){
        rp_p->active = 0;
      }
      else{
        rp_p->active = 1;
      }
      send_ack();
      //SPRL(F(" cmd0x35: active="),rp_p->active);
    break;
    
    case 0x36:  // fast mode on / off
      byte mode;
      mode=(byte)*cp - (byte)'0';
      //SPRL(F(" mode="),mode);
      mp_p->fastMode = mode;
      send_ack();
      //SPRL(F("cmd0x36: fastMode="),mp_p->fastMode);
    break;
    
    case 0x37:  // read ms-timer value 
      modbus_header();
      uint32_t ms;     // mosert sonst
      ms = millis();   // macht sonst scheiss
      //SPRL(F(" millis="),ms);
      strcat(s1,","); ltoa(ms,hs,10);      strcat(s1,hs);
      strcat(s1,",");
      modbus_trailer();
    break;

    case 0x38:  // copy all parameters from EEPROM to RAM
      // if eeprom data do not exist, use factory settings
      send_ack();   // return rv instead?? check time
      byte rv;
      rv=get_parameter();  // only if EEPROM checksum is ok, else factory settings
      //SPRL(F("eeprom get="),rv);
      if(rv==1){
        //SPRL(F("*** use factory setting"),"");
      }
    break;
    
    case 0x39:  // write all parameters from RAM to EEPROM
      send_ack();  // acknowledge first, takes some time
      eeprom_put_parameter( EEPROM_PARAMETER_ADDRESS );
      //SPRL(F("par written to eeprom;"),1);
    break;

    case 0x3A:  // RESET using watchdog - endless loop
      send_ack();  // acknowledge first, then stop the controller
      //SPRL(F("stop-loop"),);
      valve_motor_off_all();
      delay(1000);
      while(1);
    break;
    
    case 0x3B:  //  clear eeprom  ??? plpl test eeprom if ram space is left
      send_ack();    // ack first - takes some time
      eeprom_clear();
      //SPRL(F(" eeprom cleared"), "");
    break;
    

    // plpl to test
    case 0x3C:  // check if motor connected
      byte mc;
      mc = st.r[ri].motConnected;
      //mc=motor_check_connected( ri );  // check for short test-time !!! plpl
      if( mc == MOT_CONNECTED ) {mc=1;}
      else                      {mc=0;}
      modbus_header();
      strcat(s1,","); ltoa(mc,hs,10);      strcat(s1,hs);  // 1     |  1  uint8_t
      strcat(s1,",");
      modbus_trailer();
      //SPRL(F("mot connected mc="),mc);
      //Serial.print(F("mot connected mc=")); Serial.println(mc);
    break;

    case 0x3D:  // open and close valve to store times
      send_ack();  // takes too long to wait for completion
      valve_calibrate( ri );
      //SPRL(F("valve calib started"),);

    // plpl to test
    case 0x3E:  // switch off current motor
      motor_off( ri );
      send_ack();
      //SPRL(F(""),);
    break;
    
    case 0x3F:  // send motor current
      modbus_header();
      strcat(s1,","); itoa((int16_t)st.motImA,hs,10);      strcat(s1,hs);  // 1     |  1  uint8_t
      strcat(s1,",");
      modbus_trailer();
      //SPRL(F(""),);
    break;
    
    case 0x40:  // LCD-light on/off
      //Serial.print("0x40 *cp=");Serial.print(*cp);
      if(*cp=='0') {lcd_light( 0 );}
      else {lcd_light( 1 );}
      send_ack();
      //SPRL(F(""),);
    break;

    case 0x41:  // send jumper settings
      modbus_header();
      strcat(s1,","); itoa((int16_t)st.jumpers,hs,16);      strcat(s1,hs);  // 1     |  1  uint8_t
      strcat(s1,",");
      modbus_trailer();
      //SPRL(F(""),);
    break;

    
    
    // -----------------------
    default:
      send_nak();
    break;
    // -----------------------
  }

  // *** command is executed: allow new commands to be received
  st.rxCmdLen=0;              // reset count
  st.rxCmdReady = 0;          // no receiving cmd in progress
}
