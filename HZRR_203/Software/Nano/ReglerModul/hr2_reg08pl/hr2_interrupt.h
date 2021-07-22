
/*
hzrr200 interrupt service routine (ISR)
and other machine near functions
*/



#ifndef hr2_interrupt_h
#define hr2_interrupt_h

// --------------------------
// INCLUDES
// --------------------------
#include <Arduino.h>
#include <LiquidCrystal_I2C.h>
#include "DallasTemperature.h"

#include "hr2_regler.h"

//#include "hr2_brd.h"

// --------------------------
// DEFINES
// --------------------------

// --------------------------
// STRUCTURES
// --------------------------

// --------------------------
// GLOBAL VARIABLES
// --------------------------

extern LiquidCrystal_I2C  lcd;  // needed here
extern uint16_t           extended_dout;
extern DallasTemperature  sensors;

// --------------------------
// PRE-DEFINITIONS global
// --------------------------



uint16_t spi_exchange_bytes( uint16_t tosend );

void init_extended_digital_output( void );
uint8_t get_address( void );
void set_mux( byte sel );
void valve_motor( byte motor, byte dir );
void valve_motor_off_all(void);
void motor_off( uint8_t mot);
void valve_limit( byte mot, byte dir );

byte read_button(void);
byte button_INT(void);

void init_lcd4x20(void);
void lcd_logon(byte mode);
void lcd_cls(void);
void lcd_light( byte onOff );
void lcd_status(byte rNr);
void lcd_service( byte but );

float motor_current_INT(void);
byte valve_action( byte mot, byte direction, uint32_t duration, bool blocking );
void valve_startposition( byte mot );
//bool valve_ready(void);
void test_interrupt_func(void);
void valve_calibrate( byte mot );
void tic_action(void);

void blink_INT(void);
void  tic_INT(void);
void init_ds18b20(void);
float read_DS18B20( byte channel );
float get_room_temperature( void );

#endif // hr2_interrupt_h
// make sure to have a line-brak at last !!!!
