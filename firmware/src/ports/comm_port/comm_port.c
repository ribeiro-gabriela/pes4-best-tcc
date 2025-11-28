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
    tftp_decoder_task();
    
    /* server = tftp_server_create("/spiffs", 69); */
    /* tftp_server_write_set(server, 1); */
    
    /* // Task para servidor tftp */
    /* xTaskCreate((void*)tftp_server_run, "tftp_server_run", 4096, (void*)server, 5, &tftpTaskHandle); */

    return;
}

void commDeinit()
{
    wifiDeinitSoftAP();
    /* tftp_server_destroy(server); */

    return;
}
