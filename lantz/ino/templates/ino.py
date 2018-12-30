

CPP = r"""

// Import libraries
#include <Arduino.h>

#include "inodriver_bridge.h"
#include "inodriver_user.h"

#define BAUD_RATE 9600

void setup() {
  bridge_setup();
  
  user_setup();

  Serial.begin(BAUD_RATE);
}

void loop() {
  
  bridge_loop();
  
  user_loop();
}
"""


