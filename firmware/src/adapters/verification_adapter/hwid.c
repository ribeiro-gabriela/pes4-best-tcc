#include "hwid.h"

static const char* TAG = "HWID";

esp_err_t verifyPN(char* filepath)
{
    char* storedPN = readHWPNFromStorage();
    char receivedPN[SW_PN_LEN + 1];

    FILE* filePtr = fopen(filepath, "rb");
    if (filePtr == NULL)
    {
        ESP_LOGE(TAG, "Could not open file to recover hardware P/N");
        return ESP_FAIL;
    }

    if (fseek(filePtr, HW_PN_LEN, SEEK_SET) != 0)
    {
        ESP_LOGE(TAG, "Received file format does not match expected structure");
        return ESP_FAIL;
    }

    fread(receivedPN, 1, HW_PN_LEN, filePtr);
    receivedPN[HW_PN_LEN] = '\0';


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