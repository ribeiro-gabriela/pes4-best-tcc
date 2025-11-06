#ifndef FSM_CORE_H
#define FSM_CORE_H

#include <stdbool.h>
#include "freertos/FreeRTOS.h"
#include "freertos/semphr.h"

enum BC_STATES {
    OP_MODE,
    MNT_MODE
};

enum MNT_STATES {
    NOT_SET_MNT = 2,
    WAITING,
    CONNECTED,
    WAITING_AUTHORIZATION
};

enum CONN_STATES {
    NOT_SET_CONN = 5,
    WAITING_REQUEST,
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
