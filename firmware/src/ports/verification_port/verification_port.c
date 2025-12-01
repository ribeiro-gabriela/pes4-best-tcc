#include "verification_port.h"
#include "main_core.h"

extern QueueHandle_t BCQueue;

void verify(char* fileName, char* recPN, uint8_t* recHash)
{
    char filepath[64];
    QueueMessage_t msg;

    sprintf(filepath, "/spiffs/%s.bin", fileName);
    
    msg.eventID = LOG_INFO;
    sprintf((char*)msg.logMessage, "Starting verification for file %s.bin", fileName);
    if (xQueueSend(BCQueue, (void*)&msg, portMAX_DELAY) != pdPASS)
    {
        ESP_LOGE("ERROR", "Failed to send LOG_INFO message to BCQueue");
    }

    esp_err_t res;
    res = verifyPN(filepath);
    if (res != ESP_OK)
    {
        ESP_LOGE("ERROR", "Part Number verification failed");

        msg.eventID = SEC_ERR_IMG_PN_MISMATCH;
        sprintf((char*)msg.logMessage, "Image file %s Part Number is incompatible", fileName);

        if (xQueueSend(BCQueue, (void*)&msg, portMAX_DELAY) != pdPASS)
        {
            ESP_LOGE("ERROR", "Failed to send SEC_ERR_IMG_PN_MISMATCH message to BCQueue");
        }
        return;
    }

    msg.eventID = SEC_IMG_PN_OK;
    sprintf((char*)msg.logMessage, "Image file %s Part Number is compatible", fileName);

    if (xQueueSend(BCQueue, (void*)&msg, portMAX_DELAY) != pdPASS)
    {
        ESP_LOGE("ERROR", "Failed to send SEC_IMG_PN_OK message to BCQueue");
    }

    res = verifyFileIntegrity(filepath);
    if (res != ESP_OK)
    {
        msg.eventID = SEC_ERR_IMG_HASH_MISMATCH;
        sprintf((char*)msg.logMessage, "SHA-256 hash mismatch detected for file %s.bin", fileName);

        if (xQueueSend(BCQueue, (void*)&msg, portMAX_DELAY) != pdPASS)
        {
            ESP_LOGE("ERROR", "Failed to send SEC_ERR_IMG_HASH_MISMATCH message to BCQueue");
        }
        return;
    }

    msg.eventID = SEC_IMG_HASH_OK;
    sprintf((char*)msg.logMessage, "SHA-256 hash verified successfully for file %s.bin", fileName);

    if (xQueueSend(BCQueue, (void*)&msg, portMAX_DELAY) != pdPASS)
    {
        ESP_LOGE("ERROR", "Failed to send SEC_IMG_HASH_OK message to BCQueue");
    }

    return;
}