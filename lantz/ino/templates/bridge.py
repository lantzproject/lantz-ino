
IN_H_HEADER = r"""
#include <Arduino.h>

#include "SerialCommand.h"

#include "inodriver_user.h"

const char COMPILE_DATE_TIME[] = __DATE__ " " __TIME__;

void ok();
void error(const char*);
void error_i(int);
void bridge_loop();
"""

IN_CPP_HEADER = r"""
#include "inodriver_bridge.h"

SerialCommand sCmd;

void ok() {
  Serial.println("OK");
}

void error(const char* msg) {
  Serial.print("ERROR: ");
  Serial.println(msg);
}

void error_i(int errno) {
  Serial.print("ERROR: ");
  Serial.println(errno);
}

void bridge_loop() {
  while (Serial.available() > 0) {
    sCmd.readSerial();
  }
}

"""

IN_H_BODY = r"""

void getInfo();
void unrecognized(const char *);
"""

IN_CPP_BODY = r"""

//// Code 

void getInfo() {
  Serial.print("%s,");
  Serial.println(COMPILE_DATE_TIME);
}

void unrecognized(const char *command) {
  error("Unknown command");
}
//// Auto generated Feat and DictFeat Code
"""

IN_SETUP = r"""
  //// Setup callbacks for SerialCommand commands

  // All commands might return
  //    ERROR: <error message>

  // All set commands return 
  //    OK 
  // if the operation is successfull

  // All parameters are ascii encoded strings
  sCmd.addCommand("INFO?", getInfo); 

  sCmd.setDefaultHandler(unrecognized); 

"""