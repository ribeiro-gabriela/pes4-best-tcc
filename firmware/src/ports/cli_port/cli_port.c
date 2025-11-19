#include "cli_port.h"
#include "cli.h"

void cliInit()
{
    esp_err_t err = initConsole();

    if (err != ESP_OK)
    {
        ESP_LOGE("CLI PORT", "Failed to initialize CLI console");
    }

    return;
}