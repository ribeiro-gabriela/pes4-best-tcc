#include "tftp_core.h"
#include "udp.h"
#include "esp_log.h"
#include "lwip/def.h"
#include <string.h>

static const char *TAG = "tftp_decoder";

static void extract_filename(const uint8_t *payload, size_t len, char *dest, size_t max_dest_len)
{
    if (len <= 2) {
        dest[0] = '\0';
        return;
    }
    
    strncpy(dest, (char *)(payload + 2), max_dest_len - 1);
    dest[max_dest_len - 1] = '\0';
}

static void dispatch_session_task(UdpPacket_t *packet, uint16_t opcode)
{
    TftpSessionConfig_t *session_config = (TftpSessionConfig_t *)pvPortMalloc(sizeof(TftpSessionConfig_t));
    
    if (session_config == NULL) {
        ESP_LOGE(TAG, "Sem memória para criar sessão TFTP");
        return;
    }

    session_config->opcode = opcode;
    session_config->clientAddr = packet->sourceAddr;
    session_config->addrLen = packet->addrLen;
    
    extract_filename(packet->payload, packet->len, session_config->filename, sizeof(session_config->filename));

    ESP_LOGI(TAG, "starting session: %s (Opcode: %d)", session_config->filename, opcode);

    BaseType_t res = xTaskCreate(tftp_session_task, 
                                 "tftp_worker", 
                                 2 * TFTP_SESSION_STACK_SIZE, 
                                 (void *)session_config, 
                                 TFTP_SESSION_PRIORITY, 
                                 NULL);

    if (res != pdPASS) {
        ESP_LOGE(TAG, "failed to create task tftp_worker");
        vPortFree(session_config); 
    }
}

void tftp_decoder_task(void)
{
    UdpPacket_t currentPacket;
    uint16_t opcode;

    ESP_LOGI(TAG, "Decoder TFTP Iniciado. Aguardando pacotes...");

    for (;;) {
        size_t received = udpAdapterReceivePacket(&currentPacket, portMAX_DELAY);

        if (received > 0) {
            if (currentPacket.len >= 2) {
                memcpy(&opcode, currentPacket.payload, sizeof(uint16_t)); 
                opcode = ntohs(opcode); 

                switch (opcode) {
                    case TFTP_OP_RRQ:
                    case TFTP_OP_WRQ:
                        dispatch_session_task(&currentPacket, opcode);
                        break;

                    case TFTP_OP_DATA:
                    case TFTP_OP_ACK:
                    case TFTP_OP_ERROR:
                        ESP_LOGW(TAG, "session packet received (op: %d) on port 69. ignoring", opcode);
                        break;

                    default:
                        ESP_LOGW(TAG, "unknown opcode: %d", opcode);
                        break;
                }
            } else {
                ESP_LOGW(TAG, "packet too short");
            }
        }
    }
}
