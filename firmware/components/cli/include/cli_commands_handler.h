#include "esp_system.h"
#include "esp_log.h"
#include "esp_err.h"
#include "esp_spiffs.h"

#include "hashing.h"

int restart_handler(int argc, char **argv);
int ls_handler(int argc, char **argv);
int verify_sha_handler(int argc, char **argv);
int maintenance_mode_handler(int argc, char **argv);