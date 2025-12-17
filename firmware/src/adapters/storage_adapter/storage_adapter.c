#include "storage_adapter.h"
#include <stdio.h>

static const char* TAG = "STORAGE";

bool formatSpiffsData(void)
{
    esp_spiffs_format("storage");
    return 0;
}

void partitionSetup()
{
    // Initialize NVS
    esp_err_t ret = nvs_flash_init();
    if (ret == ESP_ERR_NVS_NO_FREE_PAGES || ret == ESP_ERR_NVS_NEW_VERSION_FOUND)
    {
        ESP_ERROR_CHECK(nvs_flash_erase());
        ret = nvs_flash_init();
    }
    ESP_ERROR_CHECK(ret);

    esp_vfs_spiffs_conf_t conf = {.base_path = "/spiffs",
                                  .partition_label = "storage",
                                  .max_files = 5,
                                  .format_if_mount_failed = true};

    ret = esp_vfs_spiffs_register(&conf);
    if (ret != ESP_OK)
    {
        ESP_LOGE(TAG, "Failed to initialize SPIFFS (%s)", esp_err_to_name(ret));
        return;
    }

    esp_vfs_spiffs_conf_t logs = {.base_path = "/logs",
                                  .partition_label = "logs",
                                  .max_files = 1,
                                  .format_if_mount_failed = true};

    ret = esp_vfs_spiffs_register(&logs);
    if (ret != ESP_OK)
    {
        ESP_LOGE(TAG, "Failed to initialize SPIFFS (%s)", esp_err_to_name(ret));
        return;
    }
    else
    {
        ESP_LOGI(TAG, "created %s partition", logs.base_path);
    }

    esp_vfs_spiffs_conf_t pn_conf = {.base_path = "/pn",
                                     .partition_label = "pn",
                                     .max_files = 1,
                                     .format_if_mount_failed = true};

    ret = esp_vfs_spiffs_register(&pn_conf);
    if (ret != ESP_OK)
    {
        ESP_LOGE(TAG, "Failed to initialize SPIFFS (%s)", esp_err_to_name(ret));
        return;
    }
}

char* readHWPNFromStorage()
{
    FILE* filePN = fopen("/pn/PN.txt", "r");
    if (filePN == NULL)
    {
        ESP_LOGE(TAG, "Failed to open PN file for reading");
        return NULL;
    }
    static char PN[21];
    fgets(PN, sizeof(PN), filePN);
    fclose(filePN);
    return PN;
}

void initLogFile()
{
    FILE* f = fopen("/logs/log.txt", "a");
    if (f == NULL)
    {
        ESP_LOGE(TAG, "Failed to open log file for appending");
        return;
    }
    fprintf(f, "----- New Log Session -----\n");
    fclose(f);
}
