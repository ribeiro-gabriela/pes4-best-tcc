#ifndef CLI_H
#define CLI_H

#include "esp_err.h"
#include "esp_console.h"

esp_err_t initConsole();
esp_err_t registerLog();

#endif