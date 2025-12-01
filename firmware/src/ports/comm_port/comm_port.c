#include "comm_port.h"
#include "arinc_core.h"
#include "tftp_client.h"
#include "tftp_core.h"
#include "udp.h"


struct tftp_server* server;
TaskHandle_t tftpTaskHandle = NULL;

void commInit()
{
    wifiInitSoftAP();

    initArinc();
    initUdpAdapter();
    initTaskSendLus();
    initDecoderTask();
    
    return;
}

void commDeinit()
{
    wifiDeinitSoftAP();
    deinitArinc();
    deinitUdpAdapter();
    deinitTaskSendLus();
    deinitTftpDecoderTask();
    /* tftp_server_destroy(server); */

    return;
}
