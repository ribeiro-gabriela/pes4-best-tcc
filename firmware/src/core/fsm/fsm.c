#include <stdio.h>
#include "fsm.h"

SemaphoreHandle_t stateMutex = NULL;

enum BC_STATES currentBCState = OP_MODE;
enum MNT_STATES currentMntState = NOT_SET_MNT;
enum CONN_STATES currentConnState = NOT_SET_CONN;

bool initializeFSM() {
    stateMutex = xSemaphoreCreateMutex();
    if (stateMutex == NULL) {
        return false;
    }

    return true;
}

bool setBCState(enum BC_STATES newState) {
    if (xSemaphoreTake(stateMutex, portMAX_DELAY))
    {
        currentBCState = newState;

        if (xSemaphoreGive(stateMutex) != pdTRUE)
        {
            return false;
        }
    }

    return true;
}

bool setMntState(enum MNT_STATES newState) {
    if (xSemaphoreTake(stateMutex, portMAX_DELAY))
    {
        currentMntState = newState;

        if (xSemaphoreGive(stateMutex) != pdTRUE)
        {
            return false;
        }
    }

    return true;
}

bool setConnState(enum CONN_STATES newState) {
    if (xSemaphoreTake(stateMutex, portMAX_DELAY))
    {
        currentConnState = newState;

        if (xSemaphoreGive(stateMutex) != pdTRUE)
        {
            return false;
        }
    }

    return true;
}

enum BC_STATES getBCState() {
    return currentBCState;
}

enum MNT_STATES getMntState() {
    return currentMntState;
}

enum CONN_STATES getConnState() {
    return currentConnState;
}
