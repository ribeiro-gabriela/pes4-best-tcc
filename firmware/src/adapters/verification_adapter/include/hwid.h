#ifndef HWID_H
#define HWID_H

#include <string.h>

#include "esp_err.h"
#include "storage_adapter.h"

esp_err_t verifyPN(char* filepath);

#endif