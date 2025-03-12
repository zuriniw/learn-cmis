#include <Nano33BLE_System.h>

#include "Arduino_BMI270_BMM150.h"

void setup() {
  Serial.begin(9600);
  while (!Serial);

  if (!IMU.begin()) {
    Serial.println("Failed to initialize IMU!");
    while (1);
  }
}

void loop() {
  float aX, aY, aZ, gX, gY, gZ;
  
  // check if both new acceleration and gyroscope data is
  // available
  if (IMU.accelerationAvailable() && IMU.gyroscopeAvailable()) {
    // read the acceleration and gyroscope data
    IMU.readAcceleration(aX, aY, aZ);
    IMU.readGyroscope(gX, gY, gZ);

    // print the data in CSV format
    Serial.print(aX, 3);
    Serial.print(',');
    Serial.print(aY, 3);
    Serial.print(',');
    Serial.print(aZ, 3);
    Serial.print(',');
    Serial.print(gX, 3);
    Serial.print(',');
    Serial.print(gY, 3);
    Serial.print(',');
    Serial.print(gZ, 3);
    Serial.println();
  }
}

// optional magnetometer readings
//  float mx, my, mz;
//
//  if (IMU.magneticFieldAvailable()) {
//    IMU.readMagneticField(mx, my, mz);
//
////    Serial.print("mx: "); 
//    Serial.print(mx);
//    Serial.print(' ');
////    Serial.print("my: ");
//    Serial.print(my);
//    Serial.print(' ');
////    Serial.print("mz: ");
//    Serial.print(mz);
//    Serial.print(' ');
//  } else {
//    Serial.print("(NA) ");
//  }
