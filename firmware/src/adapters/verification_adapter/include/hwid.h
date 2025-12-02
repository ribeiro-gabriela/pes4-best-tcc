#ifndef HWID_H
#define HWID_H

#include <string.h>

#include "esp_err.h"
#include "storage_adapter.h"

#define SW_PN_LEN 20
#define HW_PN_LEN 20

esp_err_t verifyPN(char* filepath);

#endif