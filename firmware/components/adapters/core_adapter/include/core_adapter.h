#ifndef CORE_ADAPTER_H
#define CORE_ADAPTER_H

#include "bc_core.h"
#include "wifi_core.h"
#include "cli.h"
#include "hashing.h"
#include "tftp.h"
#include "storage_core.h"

#include "FreeRTOS/queue.h"

typedef struct
{
    int command_id;
    char payload[256];
} QueueMessage_t;

void initializeCore();
void initializeMaintenanceMode();
void deinitMaintenanceMode();

void* stateTransitionHandler();

#endif