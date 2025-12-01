#ifndef CLI_COMMANDS_HANDLER_H
#define CLI_COMMANDS_HANDLER_H

#include "esp_system.h"
#include "esp_mac.h"
#include "esp_log.h"
#include "esp_err.h"
#include "esp_spiffs.h"

#include "hashing.h"

int restartHandler(int argc, char **argv);
int lsHandler(int argc, char **argv);
//int verifySHAHandler(int argc, char **argv);
int parkingBrakeHandler(int argc, char **argv);
int weightOnWheelsHandler(int argc, char **argv);
int maintenanceModeHandler(int argc, char **argv);
int formatHandler(int argc, char **argv);

#define TEST_COMMAND_ENABLED
#ifdef TEST_COMMAND_ENABLED
int testHandler(int argc, char **argv);
#endif

#endif