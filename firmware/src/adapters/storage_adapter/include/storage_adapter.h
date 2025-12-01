#ifndef STORAGE_CORE_H
#define STORAGE_CORE_H

#include "esp_spiffs.h"
#include "esp_err.h"
#include "esp_log.h"
#include "nvs_flash.h"

void partitionSetup();
void initLogFile();
void appendLogMessage(char* message, int length);
char* readHWPNFromStorage();

#endif