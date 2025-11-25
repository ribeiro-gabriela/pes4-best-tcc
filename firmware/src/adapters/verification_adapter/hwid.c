#include "hwid.h"

esp_err_t verifyPN(char* receivedPN)
{
    char* storedPN = readHWPNFromStorage();
    printf("Stored PN: %s\n", storedPN);
    printf("Received PN: %s\n", receivedPN);


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