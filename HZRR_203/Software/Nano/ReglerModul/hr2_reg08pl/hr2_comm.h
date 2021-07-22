
/*
 * hzrr200 communication-funktions
 * 
 * Datei "hr2_comm.h"
 * 
 * 
 * 
 */

#ifndef hr2_comm_h
#define hr2_comm_h






// --------------------------
// INCLUDES
// --------------------------
#include <Arduino.h>  //  arduino specific information
#include <stdio.h>    //  ac/ ***  i think currently unused - recheck later when u read this :)
//#include <stdarg.h>   //  ac/ used for mPrint
#include "hr2_regler.h"
#include "hr2_interrupt.h"

// --------------------------
// MACROS / DEFINES
// --------------------------
#define SER_RX_NOCMD        0
#define SER_RX_CMD          1

#define SER_TX_BUSY         0
#define SER_TX_SENT         1

#define MB_WRAP             0
#define MB_UNWRAP           1

#define MB_WRAP_READY      10
#define MB_UNWRAP_READY    11
#define MB_ADR_OK          12  
#define MB_ADR_WRONG       13

#define MB_TX_OVFL         20


// --------------------------
// STRUCTURES
// --------------------------


// --------------------------
// GLOBAL VARIABLES
// --------------------------

// --------------------------
// PRE-DECLARATIONS
// --------------------------

byte rs485_write(void);
void rs485_readln( void );
byte modbus_wrap( void );
byte modbus_unwrap(void);
void send_nak(void);
void show_param(byte mode);
void parse_cmd(void);




#endif // hr2_comm_h
// make sure to have a line-brak at last !!!!
