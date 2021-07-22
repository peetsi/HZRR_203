#ifndef LIB_LED_H
#define LIB_LED_H

#include <Arduino.h>

//SET ALL available LEDS into this const.
const unsigned int LED_PINS[] = {2, 4, 8, 3, 6};
const unsigned int LED_PINS_COUNT = 4; // 0-4

class LED {
  protected:
    enum LEDStatus {LED_AVAILABLE, LED_PIN_POSITION, LED_SELECTED, LED_SELECT, LED_ACTION, LED_OFF, LED_ON} status;
    int LED_SELECTION = -1; // will be changed to "selected"

    //unsigned long LastAction


  public:
    LED(); // Konstruktor
    void handle();
  };


/*
 * for (byte i = 0; i < 5; i = i + 1) {Serial.println(myPins[i]);
 */

LED::LED() //Konstruktor
 {
  LED_AVAIL_TOTAL       = LED_PINS[];
  LED_AVAIL_TOTAL_COUNT = LED_PINS_COUNT;
  LED_SELECTED           = -1;
  LED_COMMAND           = null;
  LED_LOG               = null;  
  LED_USR_SELECTION     = -1;
 }

void LED::handle()
{
  switch(status)
  {
    case LED_AVAILABLE:      
      return LED_PINS_COUNT;
      break;
      
    case LED_PIN_POSITION:
      return LED_PINS[];
      break;

    case LED_SELECTED:
      if (LED_SELECTION < 0) {
        return "Error, please select an LED first.\n You can do this with (LED_SELECT,ID).
      } else { return LED_SELECTION; }
    break;

    case LED_SELECT:
      if (LED_SELECT > 0) {
        LED_SELECTION = 
      }
  
  }
  
}

void LED_setPinMode( int LED_ID ) {
  pinMode(LED_ID,OUTPUT);
}

void LED_toggle( int LED_ID ) {

}

void LED_setValue( int LED_ID ) {
  
}

int LED_read( int LED_ID ) {

  
}
/*
  pinMode(ledPin, OUTPUT);     // legt den LED-Pin als Ausgang fest
  digitalWrite(ledPin, HIGH);  // LED anschalten
  delay(1000);                 // 1000 Millisekunden warten
  digitalWrite(ledPin, LOW);   // LED ausschalten
  delay(1000);                 // weitere 1000 Millisekunden warten
*/
#endif
