#include "tftp_adapter.h"
#include "freertos/FreeRTOS.h"
#include "freertos/FreeRTOSConfig_arch.h"
#include "freertos/idf_additions.h"
#include "fsm.h"
#include "portmacro.h"
#include "esp_log.h"
#include "lwip/def.h"
#include <stdint.h>
#include <string.h>


#define DECODER_TASK_STACK_SIZE 4096
static StackType_t decoderTaskStack[DECODER_TASK_STACK_SIZE];
static StaticTask_t decoderTaskStaticBuffer;
static TaskHandle_t tftpDecoderTaskHandle;

static const char *TAG = "tftp_decoder";

static void extractFilename(const uint8_t *payload, size_t len, char *dest, size_t maxDestLen)
{
    if (len <= 2) {
        dest[0] = '\0';
        return;
    }
    
    strncpy(dest, (char *)(payload + 2), maxDestLen - 1);
    dest[maxDestLen - 1] = '\0';
}

static void dispatch_session_task(UdpPacket_t *packet, uint16_t opcode)
{
    TftpSessionConfig_t *session_config = (TftpSessionConfig_t *)pvPortMalloc(sizeof(TftpSessionConfig_t));
    
    if (session_config == NULL) {
        ESP_LOGE(TAG, "no mem to create session task");
        return;
    }

    session_config->opcode = opcode;
    session_config->clientAddr = packet->sourceAddr;
    session_config->addrLen = packet->addrLen;
    
    extractFilename(packet->payload, packet->len, session_config->filename, sizeof(session_config->filename));

    ESP_LOGI(TAG, "starting session: %s (Opcode: %d)", session_config->filename, opcode);

    BaseType_t res = xTaskCreate(tftpSessionTask, 
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

void tftpDecoderTask(void* params)
{
    UdpPacket_t currentPacket;
    uint16_t opcode;

    ESP_LOGI(TAG, "packet decoder running. waiting for packets . . .");

    size_t received;

    for (;;) {
        received = udpAdapterReceivePacket(&currentPacket, portMAX_DELAY);

	
        if ((received > 0) && (getBCState() == MNT_MODE) && (getMntState() == CONNECTED)) {
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
	    vTaskDelay( 10 / portTICK_PERIOD_MS);
    }
}



int8_t initDecoderTask(void)
{
    tftpDecoderTaskHandle =
	xTaskCreateStaticPinnedToCore(tftpDecoderTask,
				      "decoder task",
				      DECODER_TASK_STACK_SIZE,
				      NULL,
				      5,
				      decoderTaskStack,
				      &decoderTaskStaticBuffer,
				      1);

    if (!tftpDecoderTaskHandle)
    {
        ESP_LOGE(TAG, "could not create tftp decoder task");
        return -1;
    }
    return 0;
}

void deinitTftpDecoderTask(void)
{
  vTaskDelete(tftpDecoderTaskHandle);
  ESP_LOGI(TAG, "deinitializing tftp decoder");
}    
