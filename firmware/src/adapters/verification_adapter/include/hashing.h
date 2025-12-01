#ifndef HASHING_H
#define HASHING_H

#include "mbedtls/sha256.h"
#include "esp_err.h"
#include "esp_log.h"
#include <stdbool.h>

#define SHA256_HASH_LEN 32
#define READ_BUFFER_SIZE 1024

#ifdef DEBUG
void func();
#endif

esp_err_t verifyFileIntegrity(char* filepath);

#endif
