#ifndef LIB_SENSOR_H
#define LIB_SENSOR_H

#include <Arduino.h>

// Constants
const float CONVERSION_NUMBER_TO_CELSIUS = 0.48828125;


/* *** readSensor( SENSOR_ID, convToCelsius ) ***
 *  
 * Reads sensor SENSOR_ID and converts it into CELSIUS 
 * CELSIUS Is a Boolean, TRUE/FALSE
 * 
 */
int readSensor( int SENSOR_ID, boolean convToCelsius=true ){
    int retVal = analogRead(SENSOR_ID);
    if (convToCelsius) {
          return retVal * CONVERSION_NUMBER_TO_CELSIUS;
    } else {
          return retVal;   
    }
}

/* *** readSensorRAW( SENSOR_ID )
 *  
 * Read Sensor Data RAW without conversion
 */
int readSensorRAW( int SENSOR_ID ){
   return analogRead(SENSOR_ID);
}


/* *** convertToCelsius( var )
 *  
 * Convert a variable to Celsius
 */
int convertToCelsius( float var ){
  return var * CONVERSION_NUMBER_TO_CELSIUS;
}

#endif
