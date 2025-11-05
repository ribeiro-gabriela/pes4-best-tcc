#include "mbedtls/sha256.h"
#include "esp_err.h"
#include "esp_log.h"
#include <stdbool.h>

#define SHA256_HASH_LEN 32
#define READ_BUFFER_SIZE 1024

#define DEBUG
#ifdef DEBUG
void func();
#endif

bool verify_file_integrity(const char* filepath, uint8_t* received_hash);
