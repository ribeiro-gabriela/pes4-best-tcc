#include "comm_port.h"
#include "arinc_adapter.h"
#include "tftp_client.h"
#include "tftp_adapter.h"
#include "udp_adapter.h"


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
