#include <dirent.h>
#include <stdio.h>
#include "string.h"

#include "cli_commands_handler.h"
#include "core_adapter.h"

static const char* TAG = "CLI";

bool mnt_mode = false;

int restart_handler(int argc, char **argv)
{
    ESP_LOGI(TAG, "Rebooting system");
    fflush(stdout);
    esp_restart();
}

int ls_handler(int argc, char **argv)
{
    DIR* dir = opendir("/spiffs");
    if (dir == NULL)
    {
        ESP_LOGE(TAG, "Failed to open directory");
        return -1;
    }

    struct dirent* entry;
    while ((entry = readdir(dir)) != NULL)
    {
        printf("FILE: %s\n", entry->d_name);
    }

    return 0;
}

int verify_sha_handler(int argc, char **argv)
{
    if (argc < 3)
    {
        ESP_LOGW(TAG, "Too few arguments");
    }
    else if (argc > 3)
    {
        ESP_LOGW(TAG, "Too many arguments");
    }
    else
    {
        if (strlen(argv[2]) != 64)
        {
            ESP_LOGW(TAG, "Invalid hash value");
            return 0;
        }
        int filepath_len = strlen(argv[1]);
        char* filepath = (char*) malloc(filepath_len + 10);
        strcpy(filepath, "/spiffs/");
        filepath[9] = '\0';
        strcat(filepath, argv[1]);

        uint8_t hash_value[32];
        char hash_str[64] = "";
        strcpy(hash_str, argv[2]);

        for (size_t i = 0; i < 32; i++)
        {
            char byte_str[3] = {0};
            byte_str[0] = hash_str[i*2];
            byte_str[1] = hash_str[i*2 + 1];

            char* end;
            long value = strtol(byte_str, &end, 16);
            if (*end != '\0')
            {
                return 1;
            }
            hash_value[i] = (uint8_t)value;
        }

        verify_file_integrity(filepath, hash_value);
    }

    return 0;
}

int maintenance_mode_handler(int argc, char **argv)
{
    if (argc < 2)
    {
        ESP_LOGW(TAG, "Too few arguments");
        return 1;
    }
    else if (argc == 2)
    {
        if (strcmp(argv[1], "enable") == 0)
        {
            if (mnt_mode)
            {
                ESP_LOGW(TAG, "Maintenance mode already enabled");
            }
            else
            {
                mnt_mode = true;
                initializeMaintenanceMode();
                ESP_LOGI(TAG, "Maintenance mode enabled");
            }

            return 0;
        }
        else if (strcmp(argv[1], "disable") == 0)
        {
            if (!mnt_mode)
            {
                ESP_LOGW(TAG, "Maintenance mode already disabled");
            }
            else
            {
                mnt_mode = false;
                deinitMaintenanceMode();
                ESP_LOGI(TAG, "Maintenance mode disabled");
            }

            return 0;
        }
    }

    ESP_LOGW(TAG, "Too many arguments");

    return 1;
}