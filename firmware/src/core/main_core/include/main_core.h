#ifndef MAIN_CORE_H
#define MAIN_CORE_H

#include <string.h>

#include "fsm_core.h"
#include "wifi_core.h"
#include "cli.h"
#include "hashing.h"
#include "tftp.h"
#include "storage_core.h"
#include "esp_mac.h"

#include "freertos/queue.h"


enum eventIDs { 
    COMM_AUTH_FAILURE,
    COMM_TIMEOUT,
    COMM_TRANSFER_COMPLETE,
    CORE_WARN_UNEXPECTED_EVENT,
    ERR_GSE_PROBE_TIMEOUT,
    ERR_AP_INIT_FAILED,
    EVENT_ABORT_MAINTENANCE_IMMEDIATE,
    EVENT_ENTER_MAINTENANCE_REQUEST,
    EVENT_SENSORS_LINK_DOWN,
    LOAD_REQUEST,
    LOG_INFO,
    SEC_ERR_GSE_AUTH_FAILED,            // Useless event, since the authentication failure is already covered by the wifi connection using wpa3
    SEC_ERR_IMG_BAD_FORMAT,
    SEC_ERR_IMG_HASH_MISMATCH,
    SEC_ERR_IMG_PN_MISMATCH,
    WIFI_AP_STARTED_OK,
    WIFI_AP_START_FAILURE_EVENT,
    WIFI_CLIENT_CONNECTED,
    WIFI_CLIENT_DISCONNECTED,
    SEC_GSE_AUTH_SUCCESS,               // New event IDs
    SEC_IMG_FORMAT_OK,
    SEC_IMG_HASH_OK,
    SEC_IMG_PN_OK
};
typedef struct
{
    enum eventIDs eventID ;
    uint8_t logMessage[256];
} QueueMessage_t;

void initializeCore();
void initializeQueue();
void initializeMaintenanceMode();
void deinitMaintenanceMode();

void* stateTransitionHandler();

#endif
