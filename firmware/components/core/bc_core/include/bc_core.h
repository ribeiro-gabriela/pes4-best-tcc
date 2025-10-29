#ifndef BC_CORE_H
#define BC_CORE_H

#include <stdbool.h>
#include "freertos/FreeRTOS.h"
#include "freertos/semphr.h"

enum BC_STATES {
    OP_MODE,
    MNT_MODE
};

enum MNT_STATES {
    WAITING = 2,
    CONNECTED,
    WAITING_AUTHORIZATION
};

enum CONN_STATES {
    WAITING_REQUEST = 5,
    CRED_EXCHANGE,
    RECEIVING_PKTS,
    IMG_VERIFICATION
};

bool initializeBCCore();

bool setBCState(enum BC_STATES newState);
bool setMntState(enum MNT_STATES newState);
bool setConnState(enum CONN_STATES newState);

enum BC_STATES getBCState();
enum MNT_STATES getMntState();
enum CONN_STATES getConnState();

#endif