#include <stdio.h>
#include "bc_core.h"

SemaphoreHandle_t stateMutex = NULL;

enum BC_STATES currentBCState = OP_MODE;
enum MNT_STATES currentMntState = WAITING;
enum CONN_STATES currentConnState = WAITING_REQUEST;

bool initializeBCCore() {
    stateMutex = xSemaphoreCreateMutex();
    if (stateMutex == NULL) {
        return false;
    }
    return true;
}

bool setBCState(enum BC_STATES newState) {
    xSemaphoreTake(stateMutex, portMAX_DELAY);
    currentBCState = newState;
    xSemaphoreGive(stateMutex);
    return true;
}

bool setMntState(enum MNT_STATES newState) {
    xSemaphoreTake(stateMutex, portMAX_DELAY);
    currentMntState = newState;
    xSemaphoreGive(stateMutex);
    return true;
}

bool setConnState(enum CONN_STATES newState) {
    xSemaphoreTake(stateMutex, portMAX_DELAY);
    currentConnState = newState;
    xSemaphoreGive(stateMutex);
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