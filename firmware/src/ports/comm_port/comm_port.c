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
    udpAdapterInit();
    initTaskSendLus();
    /* tftpDecoderTask(); */
    initDecoderTask();
    
    return;
}

void commDeinit()
{
    wifiDeinitSoftAP();
    /* tftp_server_destroy(server); */

    return;
}
