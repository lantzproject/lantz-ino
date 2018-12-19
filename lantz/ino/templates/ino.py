

CPP = r"""

// Import libraries
#include <Arduino.h>

// PERSONALIZE: Add global dependencies here.

#include "inodriver_bridge.h"
#include "inodriver_user.h"

// PERSONALIZE: Add local dependencies here.


#define BAUD_RATE 9600

void setup() {
  bridge_setup();
  
  user_setup();

  // PERSONALIZE: your setup code her

  Serial.begin(BAUD_RATE);
}

void loop() {
  
  bridge_loop();
  
  user_loop();
}
"""


