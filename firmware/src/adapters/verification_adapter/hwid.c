#include "hwid.h"

static const char* TAG = "HWID";

esp_err_t verifyPN(char* filepath)
{
    char* storedPN = readHWPNFromStorage();
    char receivedPN[21];

    FILE* filePtr = fopen(filepath, "rb");
    if (filePtr == NULL)
    {
        ESP_LOGE(TAG, "Could not open file to recover hardware P/N");
        return ESP_FAIL;
    }

    if (fseek(filePtr, 20, SEEK_SET) != 0)
    {
        ESP_LOGE(TAG, "Received file format does not match expected structure");
        return ESP_FAIL;
    }

    fread(receivedPN, 1, 20, filePtr);
    receivedPN[21] = '\0';


    ESP_LOGI(TAG, "Stored PN: %s\n", storedPN);
    ESP_LOGI(TAG, "Received PN: %s\n", receivedPN);


    if (storedPN == NULL)
    {
        return ESP_FAIL;
    }
    int i = 0;
    while (storedPN[i] != '\0' && receivedPN[i] != '\0')
    {
        if (storedPN[i] != receivedPN[i])
        {
            return ESP_FAIL;
        }
        i++;
    }

    return ESP_OK;
}