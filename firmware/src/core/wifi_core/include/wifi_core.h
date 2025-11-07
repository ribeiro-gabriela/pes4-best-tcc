#ifndef _WIFI_CORE_H
#define _WIFI_CORE_H

#include <string.h>
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "esp_mac.h"
#include "esp_wifi.h"
#include "esp_event.h"
#include "esp_log.h"
#include "nvs_flash.h"

#include "lwip/err.h"
#include "lwip/sys.h"

#define ESP_WIFI_SSID      "BC_MODULE_EMB-HW-002-021-003"
#define ESP_WIFI_PASS      "bcappassword"
#define ESP_WIFI_CHANNEL   1
#define MAX_STA_CONN       1
#define EXAMPLE_GTK_REKEY_INTERVAL 0

// WiFi AP
void wifiEventHandler(void* arg, esp_event_base_t event_base,
                        int32_t event_id, void* event_data);

void wifiInitSoftAP(void);
void wifiDeinitSoftAP(void);

#endif