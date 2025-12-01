#ifndef MAIN_CORE_H
#define MAIN_CORE_H

#include <string.h>

#include "fsm.h"
#include "comm_port.h"
#include "cli_port.h"
#include "verification_port.h"
#include "storage_port.h"
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
    SEC_ERR_GSE_AUTH_FAILED,            // Evento desnecessário, já que a autenticação é feita por WPA3-Enterprise
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
    bool parkingBrake;
    bool weightOnWheels;
    bool mntSignal;
} sensorData_t;
typedef struct
{
    enum eventIDs eventID ;
    uint8_t logMessage[256];
} QueueMessage_t;

void initializeCore();
void initializeQueue();
void initializeMaintenanceMode();
void deinitMaintenanceMode();
void initSensorPolling();

void* stateTransitionHandler();
void* sensorPolling();

#endif
