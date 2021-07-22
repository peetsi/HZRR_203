
/*
 * hzrr200 Regler EEPROM read-write
 * Datei "hr2_eeprom.h"
 * 
 * 
 * 
 */


#ifndef hr2_eeprom_h
#define hr2_eeprom_h


// --------------------------
// INCLUDES
// --------------------------

#include <EEPROM.h>


// --------------------------
// DEFINES
// --------------------------

#define EEPROM_PARAMETER_ADDRESS   0x10

// --------------------------
// STRUCTURES
// --------------------------

// --------------------------
// GLOBAL VARIABLES
// --------------------------

// --------------------------
// PRE-DEFINITIONS global
// --------------------------

void init_var_parameter(void);
void eeprom_clear( void );
void eeprom_put_parameter( uint16_t eeAddress );
void init_var_status(void);
void init_var_position( byte mode );
uint8_t get_parameter( void );

#endif  // hr2_eeprom_h
// make sure to have a line-brak at last !!!!
