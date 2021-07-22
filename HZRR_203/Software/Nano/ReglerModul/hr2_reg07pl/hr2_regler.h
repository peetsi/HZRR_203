
/*
 * hzrr200 Regler Hauptprogramm
 * Datei "hr2_regler01.h"
 * 
 * 
 * 
 */


#ifndef hr2_regler_h
#define hr2_regler_h

// --------------------------
// INCLUDES
// --------------------------
#include <Arduino.h>  //  arduino specific information
#include <SPI.h>      //  serial-peripheral interface in hardware (not bit-bang)
#include <stdio.h>    //  ac/ ***  i think currently unused - recheck later when u read this :)
//#include <stdarg.h>   //  ac/ used for mPrint
#include <ctype.h>
#include <avr/wdt.h>
#include "TimerOne.h"

#include "hr2_eeprom.h"
//#include "hr2_brd.h"
#include "hr2_interrupt.h"
#include "hr2_comm.h"
#include "hr2_doc.h"


// --------------------------
// MACROS / DEFINES
// --------------------------

// ******************************************************************************************
// VERSIONS-Informationen - ANPASSEN !!! bei Aenderungen
// ******************************************************************************************
#define   FIRMWARE_NAME     F("HZRR-200")
#define   FIRMWARE_VERSION  F("1.0.b")
#define   FIRMWARE_DATE     F("2020-09-26")
#define   HARDWARE_VERSION  F("1.4")
#define   HARDWARE_DATE     F("2020-03-31")
// ******************************************************************************************

// ******************************************************************************************
#define EEPROM_CLEAR   0   // clear eeprom after start and use factory settings
// ******************************************************************************************


// *** system, debug

//#define SPR(x,y)
//#define SPRL(x,y)
#define SPR(x,y)  {Serial.print(x);Serial.print(y);}
#define SPRL(x,y) {Serial.print(x);Serial.println(y);}
#define LCDP(s,z,text) {lcd.setCursor(s,z);lcd.print(text);}

// *** MC-Module selection - uncomment one suitable for Microcontroller module used
#define   ARDUINO_NANO  1  // Arduino Nano R3 with CH340C USB/serieal converter chip
#define   ESP32_CV4     0  // ESP32 dev. Board with WLAN // TODO later implementation

// *** MC pin definitions
//#if ARDUINO_NANO == 1
#define   vVent1_PIN  2
#define   vVent2_PIN  3
#define   OW_PIN      4
#define   DHT22_PIN   5
#define   SERVO1_PIN  6
#define   SRQ_PIN     7
#define   nPL_PIN     8    // strapped from: SERVO2_PIN
#define   FAN_PWM_PIN 9
#define   DE485_PIN   10
#define   MOSI_PIN    11
#define   MISO_PIN    12
#define   SCK_PIN     13
#define   Vmot2_PIN   A0
#define   MOTCURR_PIN A1
#define   VDC11_PIN   A2
#define   SWITCH_PIN  A3
#define   SDA_PIN     A4
#define   SCL_PIN     A5
#define   ANAIN1_PIN  A6
#define   ANAIN2_PIN  A7
#define   ADC_RANGE   (0x03FF);   // 10 bit conversion
//#endif

//#elif ESP32_CV4 == 1
// not yet implemented
// add pins here
//#define   ADC_RANGE   (0x0FFF);   // 12 bit conversion
//#endif

// *** serial data protocol RS485 network
#define   PROT_REV      'b'       // revision of protocol in case of later changes
#define   MBWRAP         0        // ac/
#define   MBUNWRAP       1        // ac/
#define   MAX_STR_LEN   64
#define   SERIAL_TIMEOUT   100    // ms;   break receiving string via RS485
// RX_ / TX_CMD - ac/ begin
#define   STR_RX_MAXLEN     64
#define   STR_RX_ARR_MAXLEN 65    // 64?
#define   STR_RX_TTL        50    // ms; TTL?
#define   STR_TX_MAXLEN     64

// *** for DS18B20 digital one-wire temperature sensors
// use OW_PIN for one-wire (see pin definitions)
#include "OneWire.h"
#include "DallasTemperature.h"

// *** extended digital output bits
//     i/o pins are not enough on MC; so 16bit are shifted out for 
//     extra digital outputs and 8bits are shifted in using SPI
//
// Multiplexer to switch up to 8 DS18B20 one-wire temp. sensors
//        name     bit-nr.
#define   MUX_A0     0x0001   // multiplexer address 0
#define   MUX_A1     0x0002   // multiplexer address 1
#define   MUX_A2     0x0004   // multiplexer address 2
#define   MUX_EN     0x0008   // multiplexer enable
// H-bridges to switch valve motors to "open - stop - close" valve 
#define   HB_M0A     0x0020   // half-bridge motor 0 line A
#define   HB_M0B     0x0010   // half-bridge motor 0 line B
#define   HB_M1A     0x0040   // half-bridge motor 1 line A
#define   HB_M1B     0x0080   // half-bridge motor 1 line B
#define   HB_M2A     0x0200   // half-bridge motor 2 line A
#define   HB_M2B     0x0100   // half-bridge motor 2 line B
// switch on thermometer voltage for pt10#d00 sensor / room sensor
#define   V_THERM    0x0400   // low -> voltage on

// *** message flags
// serial communication
#define MSG_COM_RX_WSA          1   // wrong sub-address
#define MSG_COM_RX_WPROT        2   // wrong protocol
#define MSG_COM_RX_WLRC         4   // wrong LRC check
#define MSG_COM_RX_WCS          8   // wrong cecksum check
#define MSG_COM_TX_OVF         16   // tx-string is too long
//#define MSG_COM_RX_W
//#define MSG_COM_RX_W

// module

// each regulator
#define   MSG_MOT_NOT_CONNECTED   0x0001

// *** system related
#define LCD_REFRESH           500L   // msec;  time to refresh LCD
#define LCD_SERVICE_TO  10L*60000L   // msec;  timeout to leave service LCD screen

// *** application related
// test related - ac/   {void Hzrr200brd::test_Run(int id) -> brd.cpp}
#define   IBT_VERSION     11
#define   IBT_MOD_ADDRESS 12
#define   IBT_LCD         13
#define   IBT_TASTER      14
#define   IBT_TEMPSENSOR  15
#define   IBT_MOTOR       16
#define   IBT_RS485       17

// *** motor control and status 
#define   MOT_STOP      20
#define   MOT_CLOSE     21
#define   MOT_OPEN      22
#define   MOT_MARKED    23
#define   MOT_FREE      24    // ATTENTION: != 0,1 or 2 !!
#define   MOT_BUSY      25
#define   MOT_STARTED   26
#define   MOT_WRONG_NR  27
#define   MOT_WRONG_DIR 28
#define   MOT_POS_DELTA 29    // motor difference
#define   MOT_POS_LIMIT 30    // motor limit position
// STATUS
#define   MOT_NOT_ACTIVE     40
#define   MOT_STARTPOS       41
#define   MOT_NOT_TESTED     42
#define   MOT_CONNECTED      43
#define   MOT_NOT_CONNECTED  44
//#define   MOT_OPEN_LIMIT     45

// *** measured values related
// room temperature
#define   TEMP_ROOM_AUTO      50
#define   TEMP_ROOM_DAY       51
#define   TEMP_ROOM_NIGHT     52
#define   TEMP_ROOM_STANDBY   53
#define   TEMP_NO_VALUE     -129

// *** watchdog
#define WD_TIC_ACTION  0x01
#define WD_LCD_REFRESH 0x02
#define WD_GET_ADDRESS 0x04
#define WD_LCD_DISPLAY 0x08

#define WD_KEY_CHECK  (WD_TIC_ACTION | WD_LCD_REFRESH | WD_GET_ADDRESS | WD_LCD_DISPLAY)


// *** macros
#define   DIFF(a,b)   ((long)(a - b))
#define   EXPIRED(t)  (DIFF(millis(),t)>=0)


// --------------------------
// STRUCTURES
// --------------------------
// *** global structures

// *** status information for all kind of tasks
// (ee) save data to EEPROM TODO
// status for each Regulator
typedef struct {
  byte        active;          // 1;     0:module inactive, else:active
  // valve-motor control; interrupt will automatically start if motor free
  byte        motConnected;    // MOT_NOT_TESTED, MOT_NOT_CONNECTED, MOT_CONNECTED 
  uint8_t     motStart;        // 1 if motor shall be started, else 0; reset by ISR after motor stop
  uint8_t     motDir;          // one of MOT_STOP, MOT_CLOSE, MOT_OPEN; ISR sets it to MOT_STOP after motor stop
  uint8_t     motReady;        // 1      this motor has reached its poition
  uint32_t    tMotDur;         // ms;    exact duration time - motor has to run this time.
  float       motPos;          // 1;     0..999 close..open;relative motor position; set on motor movement and limits
  // valve-motor status
  uint8_t     motLimit;        // MOT_STOP, MOT_STARTPOS, MOT_CLOSE or MOT_OPEN if limit reached; ("last direction")
  // regulator variables  
  bool        firstLoop;       // bool;  1 if first loop is in progress; used for low-pass filters
  float       tempVlMeas;      // degC;  temperature Vorlauf, locally measured; not used / was used if no central temp. received
  float       tempVl;          // degC;  temperature Vorlauf, used value (see status_t .tempVlRx !)
  float       tempVlLP1;       // degC;  temperature Vorlauf, after passing a low-pass filter
  char        season;          // 'W'/'S' for winter / summer; in summer no regulation if VL < tv0
  float       tempSoll;        // degC;  set value for Ruecklauf; case Rommtemp: set value for RT
  float       tempRlMeas;      // degC;  temperature Ruecklauf, measured value "Istwert" ungefiltert
  float       tempRlLP1;       // degC;  temperature Ruecklauf, after passing 1st low-pass filter
  float       tempRlLP2;       // degC;  temperature Ruecklauf, after passing 2nd order low-pass filter
  float       tempRlLP2Old;    // degC;  prvious value of tempRlLP2
  float       dKSum;           // Ksec;  Kelvin*sec, integral-sum of temp. differences exceeding tolerance band
  float       mRl;             // K/s;   slope of Ruecklauf temp. change over time
  float       mRlLP1;          // K/s;   slope of Ruecklauf temp. change over time, low-pass 1st order
  uint32_t    mPauseEnd;       // ms;    endtime to pause motor action if an m-slope was too steep
  byte        mPause;          // bool   true if motor-action is paused
  uint32_t    motBoostEnd;     // ms;    endtime to boost water flow
  byte        motBoost;        // bool;  true if valve was opened for boost
  // motor
  byte        motGotoStart;    // 1;     1:marked to go; increment state
  byte        motCalib;        // 1;     1:start motor time-calibration; increment state
  uint32_t    tStart;          // ms;    start-time for valve movement
  // message
  uint16_t    msg;             // ;      Bit-array; for each message (error) set a different bit
  } regStatus_t;


typedef struct {
  // for the module:
  byte     jumpers;       // 1;     jumper settings; bitwise
  byte     tic;           // bool   set by timer1 ISR; >0: perform urgent tasks 
  byte     modAddr;       // 1;     module address from jumper settings
  byte     comefrom;      // ;      1=there was a restart and parameters have to be set from EEPROM
  uint32_t tNextMeas;     // ms;    time when next measurement has to be performed
  // error numbers
  uint32_t errCom;        // ;      communication errors
  uint32_t errMod;        // ;      module errors
  // measured values
  byte     cmdAddress;    // ;      Address of the last received command
  // temperature Vorlauf from heating central
  float    tempVlRx;      // degC;  via network received central Vorlauf temperatrue
  uint32_t tVlRxEnd;      // ms;    end-time until tempVlRx is valid; use local VL values after this time

  // rx (received) command variables, received from master
  byte     rxCmdNr;                // command nr derived from command string
  uint8_t  rxReg;                  // command for: 0=module, 1=regler0, 2=regler1, 3=regler2,..
  char     rxBuf[STR_RX_MAXLEN];   // receive buffer for incoming chars
  byte     rxCmdReady;             // 0:no, 1: in progress, 2: ready receiving a command
  int      rxCmdLen;               // length of received command
  uint32_t rxTTL;                  // set time to live after receiving the first ':' (timeout)
  int16_t  rxAdr;                  // address of receiver of data packet, -1 if not valid
  //int16_t  rxSenderAdr;            // address of sender of data packet

  // tx (send) Command variables; send to master
  //byte     txCmdSend;              // if 1 then send; tx function resets it to 0
  byte     txCmdNr;                // repeat command nr from master
  byte     txReg;                  // 0=module; 1,2,3 for regulator 0,1,2
  //char     txCmd[STR_TX_MAXLEN];   // contains command-string to be wrapped    
  char     txBuf[STR_TX_MAXLEN];   // contains complete command-string to be sent    
  //char     txCmd[STR_TX_MAXLEN];   // contains complete command-string under construction    
  byte     txCmdRunning;           // 0 if not running, 1 while sending is in progress - txBu not free
  
  // wrapper
  char     modbWrapped[64];

  // variables for running ONE motor
  //   for technical (low total current) reasons only one motor can run at a time; 
  //   the regulator status sets a request for its correlated motor-valve to run in <direction> for <time> msec.
  //   the ISR looks at these data and controls one motor after the other;
  //   following variables are used for this
  int16_t  adMot2;                  // 1;     half the motor supply voltage: 3.3V / 2 = 1.65V typ.  
  byte     motRunning;              // motor nr. 0,1,2 if motor is running; else MOT_FREE
  int16_t  motAD;                   // 1;     voltage from shunt-resistor to measure motor current
  bool     motReady;                // ;      true if last movement is completed (for handshake with ISR)  
  byte     motDir;                  // ;      direction to move; MOT_STOP, MOT_CLOSE, MOT_OPEN valve
  uint32_t tMotEnd;                 // ms     stop running motor if time is reached
  uint32_t tMotDelayEnd;            // ms;    do not measure motor current before - skip motor-on current peak 
  uint16_t motIMin;                 // mA;    above: normal operation of motor; below: open circuit assumed 
  uint16_t motIMax;                 // mA;    above: mechanical limit reached; 2 x above: short circuit assumed
  float    motUsV;                  // V;     supply voltage of motor; 3.3V nom. - used to calculate motor current
  float    motImA;                  // mA;    measured Motorcurrent
  //float    motImAOld;               // mA;    previusly measured Motorcurrent for low-pass calculation
  //float    motImALP;                // mA;    motor current after slight low-pass    
  byte     motStop;                 // 1;     1 stop current motor; ISR will stop motor at once

  // button switches
  byte     but;                     // 1;     Nr. of button pressed e {1,2,3,4,5}, 0 = none
  byte     butOld;                  // 1;     previous button value
  byte     butPressed;              // 1;     button was pressed, change from 0 to button number
  
  // LCD
  byte     lcdService;              // 1;     LCD-mode: 0 Status, 1=service new, 2=service running
  char     smm;                     // 1;     LCD Service: Index for motor selection in first line
  char     smf;                     // 1;     LCD Service: Index for function selection in second line
  uint32_t smTEnd;                  // ms;    LCD Service: menu endtime 
  uint32_t backLightEnd;            // ms;    LCD time to switch off backlight
  uint32_t tLcdRefresh;             // ms;    LCD next time to be refreshed

  // temperature
  uint32_t    tDs18b20End;          // ms;    End of conversion time after start-conversion signal
  
  // messages
  uint16_t msg;                     // ;      Bit-array; for each message (error) set a different bit

  // for all regulators
  float    tempRlSoll ;             // degC;  temperature Ruecklauf "Sollwert"
  byte     iTemp;                   // 1;     index for temperature sensors
  // for regulator 2 - regulator-index 1
  byte     roomReg;                 // 1;     true if a room-regulation is acteive for regulator 1
  float    rTemp;                   // degC;  room-temperature from Thermostat; +/-4K due to tuning
  byte     rMode;                   // ;      Schalter Stellung an der Raumthermostat Fernbedienung

  // for each regulator
  regStatus_t r[3];
  uint16_t wdKey;                   // ;      watchdog key for passing different stations
} status_t;



// *** parameters
//     all parameters are also stored in EEPROM
//     they can be changed via network
// status for each regulator
typedef struct {
  uint8_t  active;        // 0=inactive; 1=active (factory setting)
  // valve motor
  int16_t  motIMin;       // mA;    above: normal operation; below: open circuit 
  int16_t  motIMax;       // mA;    above: mechanical limit; 2x: short circuit
  int16_t  tMotDelay;     // ms;    motor current measure delay; (peak current)
  uint16_t tMotMin;       // ms;    minimum motor-on time; shorter does not move
  uint8_t  tMotMax;       // sec;   timeout to reach limit; stop if longer
  uint8_t  dtOpen;        // sec;   time from limit close to limit open
  uint8_t  dtClose;       // sec;   time from limit open to limit close
  uint16_t dtOffset;      // ms;    time to open valve for startposition
  uint16_t dtOpenBit;     // ms;    time to open valve a bit if closed is reached

  // regulation
  float    pFakt;         // s/K;   P-factor; motor-on time per Kelvin diff.
  float    iFakt;         // 1/K;   I-factor;
  float    dFakt;         // s2/K;  D-factor; 
  float    tauTempVl;     // sec;   tau; reach 1/e; low-pass (LP) filter Vorlauf
  float    tauTempRl;     // sec;   tau; reach 1/e; LP filter Ruecklauf (RL)
  float    tauM;          // sec;   tau; reach 1/e; LP filter slope m
  float    m2hi;          // mK/s;  up-slope; stop motor if above for some time 
  float    m2lo;          // mK/s;  down-slope; open valve a bit
  uint16_t tMotPause;     // sec;   time to stop motor after m2hi
  uint16_t tMotBoost;     // sec;   time to keep motor open after m2lo increase flow
  uint16_t dtMotBoost;    // ms;    motor-on time to open motor-valve for boost
  uint16_t dtMotBoostBack;// ms;    motor-on time to close motor-valve after boost
  float    tempTol;       // K;     temperature tolerance allowed for Ruecklauf

} regParam_t;


// parameter of the whole program
// NOTE: sizeof(par) = 317 byte 
typedef struct {
  // for the module:
  uint16_t timer1Tic;              // ms;    Interrupt heartbeat of Timer1     
  uint16_t tMeas;                  // sec;   measuring interval
  uint8_t dtBackLight;             // min;   LCD time to switch off backlight
  uint8_t fastMode;                // 1;     0:normal speed; else:faster for test

  // common to all regulators
  // characteristic curve (Kennlinie)
  float    tv0,tv1,tr0,tr1;        // degC;  see function characteristic()
  uint8_t tVlRxValid;              // min;    st.tempVlRx is valid this time;
  // regulator 2 (index 1): special Zimmer temperature; used if jumper 128 ist installed:
  float    tempZiSoll;             // degC;  Zimmer temp. soll; +/-4K with room Thermostat
  float    tempZiTol  ;            // degC;  toleracne for room-temperature
  
  // for each regulator:
  regParam_t r[3];
  uint32_t checksum;               // has to be in last place for eeprom check!
} parameter_t;



typedef struct {  
  uint16_t nBoot;            // 1;     number of power-on boot 
  uint16_t nMotLimit[3];     // 1;     count of limit-drives of motor  
  float    tMotTotal[3];     // sec;   total motor-on time 
  uint16_t checksum;         //
} statistic_t;




// --------------------------
// GLOBAL VARIABLES
// --------------------------
extern status_t        st;
extern parameter_t     par;
extern statistic_t     statist;

// TODO: ee - store in EEPROM
// for each Regulator


// --------------------------
// PRE-DECLARATIONS
// --------------------------
int freemem(void);
byte regler( byte reg );
float characteristic( float tv );  
void valve_motor( byte motor, byte dir );
byte motor_check_connected( byte motor );
void read_temperature(void);

void test_interrupt_func();






#endif // hr2_regler01_h
// make sure to have a line-brak at last !!!!
