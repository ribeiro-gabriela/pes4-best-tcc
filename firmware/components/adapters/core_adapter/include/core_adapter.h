#ifndef CORE_ADAPTER_H
#define CORE_ADAPTER_H

#include <string.h>

#include "bc_core.h"
#include "wifi_core.h"
#include "cli.h"
#include "hashing.h"
#include "tftp.h"
#include "storage_core.h"
#include "esp_mac.h"

#include "FreeRTOS/queue.h"


enum eventIDs { 
    COMM_AUTH_FAILURE,
    COMM_TIMEOUT,
    COMM_TRANSFER_COMPLETE,
    CORE_WARN_UNEXPECTED_EVENT,
    ERR_GSE_PROBE_TIMEOUT,
    EVENT_ABORT_MAINTENANCE_IMMEDIATE,
    EVENT_ENTER_MAINTENANCE_REQUEST,
    EVENT_SENSORS_LINK_DOWN,
    LOAD_REQUEST,
    LOG_INFO,
    SEC_ERR_GSE_AUTH_FAILED,
    SEC_ERR_IMG_BAD_FORMAT,
    SEC_ERR_IMG_HASH_MISMATCH,
    SEC_ERR_IMG_PN_MISMATCH,
    WIFI_AP_STARTED_OK,
    WIFI_AP_START_FAILURE_EVENT,
    WIFI_CLIENT_CONNECTED,
    WIFI_CLIENT_DISCONNECTED
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