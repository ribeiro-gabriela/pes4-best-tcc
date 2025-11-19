#include <dirent.h>
#include <stdio.h>
#include "string.h"

#include "cli_commands_handler.h"
#include "main_core.h"

static const char* TAG = "CLI";

extern QueueHandle_t BCQueue;

sensorData_t sensors = {false, false, false};

int restartHandler(int argc, char **argv)
{
    ESP_LOGI(TAG, "Rebooting system");
    fflush(stdout);
    esp_restart();
}

int lsHandler(int argc, char **argv)
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

int verifySHAHandler(int argc, char **argv)
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
        char hash_str[65] = "";
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

        verifyFileIntegrity(filepath, hash_value);
    }

    return 0;
}

int parkingBrakeHandler(int argc, char **argv)
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
            sensors.parkingBrake = true;
            ESP_LOGI(TAG, "Parking brake set to engaged");
            checkMaintenanceMode();
        }
        else if (strcmp(argv[1], "disable") == 0)
        {
            sensors.parkingBrake = false;
            ESP_LOGW(TAG, "Parking brake set to released");
            checkMaintenanceMode();
        }
        return 0;
    }

    ESP_LOGW(TAG, "Too many arguments");
    
    return 1;
}

int weightOnWheelsHandler(int argc, char **argv)
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
            sensors.weightOnWheels = true;
            ESP_LOGI(TAG, "Weight on wheels set to true");
            checkMaintenanceMode();
        }
        else if (strcmp(argv[1], "disable") == 0)
        {
            sensors.weightOnWheels = false;
            ESP_LOGW(TAG, "Weight on wheels set to false");
            checkMaintenanceMode();
        }

        return 0;
    }

    ESP_LOGW(TAG, "Too many arguments");
    
    return 1;
}

int maintenanceModeHandler(int argc, char **argv)
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
            if (getBCState() == MNT_MODE)
            {
                ESP_LOGW(TAG, "Maintenance lever already enabled");
            }
            else
            {
                sensors.mntSignal = true;
                ESP_LOGI(TAG, "Maintenance lever enabled");
                checkMaintenanceMode();
            }
        }
        else if (strcmp(argv[1], "disable") == 0)
        {
            sensors.mntSignal = false;
            
            ESP_LOGW(TAG, "Maintenance lever disabled");
            checkMaintenanceMode();
        }

        return 0;
    }

    ESP_LOGW(TAG, "Too many arguments");

    return 1;
}

void checkMaintenanceMode()
{
    QueueMessage_t msg;

    if (sensors.mntSignal && sensors.parkingBrake && sensors.weightOnWheels)
    {
        if (getBCState() != MNT_MODE)
        {
            ESP_LOGI(TAG, "All conditions met for maintenance mode. Enabling maintenance mode.");

            msg.eventID = EVENT_ENTER_MAINTENANCE_REQUEST;
            sprintf((char*)msg.logMessage, "%lu: Maintenance mode enabled via sensor conditions", esp_log_early_timestamp());

            if (xQueueSend(BCQueue, (void*) &msg, portMAX_DELAY) != pdPASS)
            {
                ESP_LOGE(TAG, "Failed to send message to BCQueue");
            }
        }
    }
    else
    {
        if (getBCState() == MNT_MODE)
        {
            ESP_LOGI(TAG, "Conditions not met for maintenance mode. Disabling maintenance mode.");

            msg.eventID = EVENT_ABORT_MAINTENANCE_IMMEDIATE;
            sprintf((char*)msg.logMessage, "%lu: Maintenance mode disabled via sensor conditions", esp_log_early_timestamp());

            if (xQueueSend(BCQueue, (void*) &msg, portMAX_DELAY) != pdPASS)
            {
                ESP_LOGE(TAG, "Failed to send message to BCQueue");
            }
        }
    }

}

#define TEST_COMMAND_ENABLED
#ifdef TEST_COMMAND_ENABLED
int testHandler(int argc, char **argv)
{
    if (argc < 2)
    {
        ESP_LOGW(TAG, "Too few arguments");
        return 1;
    }
    else if (argc == 2)
    {
        ESP_LOGI(TAG, "Test command executed");

        QueueMessage_t msg;
        int testInput = atoi(argv[1]);
        printf("Test input: %d\n", testInput);

        if (testInput == COMM_AUTH_FAILURE)
        {
            msg.eventID = COMM_AUTH_FAILURE;
            sprintf((char*)msg.logMessage, "(%lu) TEST: COMM_AUTH_FAILURE sent to queue", esp_log_early_timestamp());
            if (xQueueSend(BCQueue, (void*)&msg, portMAX_DELAY) != pdPASS)
            {
                ESP_LOGE("ERROR", "Failed to send COMM_AUTH_FAILURE message to BCQueue");
            }
            vTaskDelay(100 / portTICK_PERIOD_MS);
        }
        else if (testInput == COMM_TIMEOUT)
        {
            msg.eventID = COMM_TIMEOUT;
            sprintf((char*)msg.logMessage, "(%lu) TEST: COMM_TIMEOUT sent to queue", esp_log_early_timestamp());
            if (xQueueSend(BCQueue, (void*)&msg, portMAX_DELAY) != pdPASS)
            {
                ESP_LOGE("ERROR", "Failed to send COMM_TIMEOUT message to BCQueue");
            }
            vTaskDelay(100 / portTICK_PERIOD_MS);
        }
        else if (testInput == COMM_TRANSFER_COMPLETE)
        {
            msg.eventID = COMM_TRANSFER_COMPLETE;
            sprintf((char*)msg.logMessage, "(%lu) TEST: COMM_TRANSFER_COMPLETE sent to queue", esp_log_early_timestamp());
            if (xQueueSend(BCQueue, (void*)&msg, portMAX_DELAY) != pdPASS)
            {
                ESP_LOGE("ERROR", "Failed to send COMM_TRANSFER_COMPLETE message to BCQueue");
            }
            vTaskDelay(100 / portTICK_PERIOD_MS);
        }
        else if (testInput == CORE_WARN_UNEXPECTED_EVENT)
        {
            msg.eventID = CORE_WARN_UNEXPECTED_EVENT;
            sprintf((char*)msg.logMessage, "(%lu) TEST: CORE_WARN_UNEXPECTED_EVENT sent to queue", esp_log_early_timestamp());
            if (xQueueSend(BCQueue, (void*)&msg, portMAX_DELAY) != pdPASS)
            {
                ESP_LOGE("ERROR", "Failed to send CORE_WARN_UNEXPECTED_EVENT message to BCQueue");
            }
            vTaskDelay(100 / portTICK_PERIOD_MS);
        }
        else if (testInput == ERR_GSE_PROBE_TIMEOUT)
        {
            msg.eventID = ERR_GSE_PROBE_TIMEOUT;
            sprintf((char*)msg.logMessage, "(%lu) TEST: ERR_GSE_PROBE_TIMEOUT sent to queue", esp_log_early_timestamp());
            if (xQueueSend(BCQueue, (void*)&msg, portMAX_DELAY) != pdPASS)
            {
                ESP_LOGE("ERROR", "Failed to send ERR_GSE_PROBE_TIMEOUT message to BCQueue");
            }
            vTaskDelay(100 / portTICK_PERIOD_MS);
        }
        else if (testInput == ERR_AP_INIT_FAILED)
        {
            msg.eventID = ERR_AP_INIT_FAILED;
            sprintf((char*)msg.logMessage, "(%lu) TEST: ERR_AP_INIT_FAILED sent to queue", esp_log_early_timestamp());
            if (xQueueSend(BCQueue, (void*)&msg, portMAX_DELAY) != pdPASS)
            {
                ESP_LOGE("ERROR", "Failed to send ERR_AP_INIT_FAILED message to BCQueue");
            }
            vTaskDelay(100 / portTICK_PERIOD_MS);
        }
        else if (testInput == EVENT_ABORT_MAINTENANCE_IMMEDIATE)
        {
            msg.eventID = EVENT_ABORT_MAINTENANCE_IMMEDIATE;
            sprintf((char*)msg.logMessage, "(%lu) TEST: EVENT_ABORT_MAINTENANCE_IMMEDIATE sent to queue", esp_log_early_timestamp());
            if (xQueueSend(BCQueue, (void*)&msg, portMAX_DELAY) != pdPASS)
            {
                ESP_LOGE("ERROR", "Failed to send EVENT_ABORT_MAINTENANCE_IMMEDIATE message to BCQueue");
            }
            vTaskDelay(100 / portTICK_PERIOD_MS);
        }
        else if (testInput == EVENT_ENTER_MAINTENANCE_REQUEST)
        {
            msg.eventID = EVENT_ENTER_MAINTENANCE_REQUEST;
            sprintf((char*)msg.logMessage, "(%lu) TEST: EVENT_ENTER_MAINTENANCE_REQUEST sent to queue", esp_log_early_timestamp());
            if (xQueueSend(BCQueue, (void*)&msg, portMAX_DELAY) != pdPASS)
            {
                ESP_LOGE("ERROR", "Failed to send EVENT_ENTER_MAINTENANCE_REQUEST message to BCQueue");
            }
            vTaskDelay(100 / portTICK_PERIOD_MS);
        }
        else if (testInput == EVENT_SENSORS_LINK_DOWN)
        {
            msg.eventID = EVENT_SENSORS_LINK_DOWN;
            sprintf((char*)msg.logMessage, "(%lu) TEST: EVENT_SENSORS_LINK_DOWN sent to queue", esp_log_early_timestamp());
            if (xQueueSend(BCQueue, (void*)&msg, portMAX_DELAY) != pdPASS)
            {
                ESP_LOGE("ERROR", "Failed to send EVENT_SENSORS_LINK_DOWN message to BCQueue");
            }
            vTaskDelay(100 / portTICK_PERIOD_MS);
        }
        else if (testInput == LOAD_REQUEST)
        {
            msg.eventID = LOAD_REQUEST;
            sprintf((char*)msg.logMessage, "(%lu) TEST: LOAD_REQUEST sent to queue", esp_log_early_timestamp());
            if (xQueueSend(BCQueue, (void*)&msg, portMAX_DELAY) != pdPASS)
            {
                ESP_LOGE("ERROR", "Failed to send LOAD_REQUEST message to BCQueue");
            }
            vTaskDelay(100 / portTICK_PERIOD_MS);
        }
        else if (testInput == LOG_INFO)
        {
            msg.eventID = LOG_INFO;
            sprintf((char*)msg.logMessage, "(%lu) TEST: LOG_INFO sent to queue", esp_log_early_timestamp());
            if (xQueueSend(BCQueue, (void*)&msg, portMAX_DELAY) != pdPASS)
            {
                ESP_LOGE("ERROR", "Failed to send LOG_INFO message to BCQueue");
            }
            vTaskDelay(100 / portTICK_PERIOD_MS);
        }
        else if (testInput == SEC_ERR_GSE_AUTH_FAILED)
        {
            msg.eventID = SEC_ERR_GSE_AUTH_FAILED;
            sprintf((char*)msg.logMessage, "(%lu) TEST: SEC_ERR_GSE_AUTH_FAILED sent to queue", esp_log_early_timestamp());
            if (xQueueSend(BCQueue, (void*)&msg, portMAX_DELAY) != pdPASS)
            {
                ESP_LOGE("ERROR", "Failed to send SEC_ERR_GSE_AUTH_FAILED message to BCQueue");
            }
            vTaskDelay(100 / portTICK_PERIOD_MS);
        }
        else if (testInput == SEC_ERR_IMG_BAD_FORMAT)
        {
            msg.eventID = SEC_ERR_IMG_BAD_FORMAT;
            sprintf((char*)msg.logMessage, "(%lu) TEST: SEC_ERR_IMG_BAD_FORMAT sent to queue", esp_log_early_timestamp());
            if (xQueueSend(BCQueue, (void*)&msg, portMAX_DELAY) != pdPASS)
            {
                ESP_LOGE("ERROR", "Failed to send SEC_ERR_IMG_BAD_FORMAT message to BCQueue");
            }
            vTaskDelay(100 / portTICK_PERIOD_MS);
        }
        else if (testInput == SEC_ERR_IMG_HASH_MISMATCH)
        {
            msg.eventID = SEC_ERR_IMG_HASH_MISMATCH;
            sprintf((char*)msg.logMessage, "(%lu) TEST: SEC_ERR_IMG_HASH_MISMATCH sent to queue", esp_log_early_timestamp());
            if (xQueueSend(BCQueue, (void*)&msg, portMAX_DELAY) != pdPASS)
            {
                ESP_LOGE("ERROR", "Failed to send SEC_ERR_IMG_HASH_MISMATCH message to BCQueue");
            }
            vTaskDelay(100 / portTICK_PERIOD_MS);
        }
        else if (testInput == SEC_ERR_IMG_PN_MISMATCH)
        {
            msg.eventID = SEC_ERR_IMG_PN_MISMATCH;
            sprintf((char*)msg.logMessage, "(%lu) TEST: SEC_ERR_IMG_PN_MISMATCH sent to queue", esp_log_early_timestamp());
            if (xQueueSend(BCQueue, (void*)&msg, portMAX_DELAY) != pdPASS)
            {
                ESP_LOGE("ERROR", "Failed to send SEC_ERR_IMG_PN_MISMATCH message to BCQueue");
            }
            vTaskDelay(100 / portTICK_PERIOD_MS);
        }
        else if (testInput == WIFI_AP_STARTED_OK)
        {
            msg.eventID = WIFI_AP_STARTED_OK;
            sprintf((char*)msg.logMessage, "(%lu) TEST: WIFI_AP_STARTED_OK sent to queue", esp_log_early_timestamp());
            if (xQueueSend(BCQueue, (void*)&msg, portMAX_DELAY) != pdPASS)
            {
                ESP_LOGE("ERROR", "Failed to send WIFI_AP_STARTED_OK message to BCQueue");
            }
            vTaskDelay(100 / portTICK_PERIOD_MS);
        }
        else if (testInput == WIFI_AP_START_FAILURE_EVENT)
        {
            msg.eventID = WIFI_AP_START_FAILURE_EVENT;
            sprintf((char*)msg.logMessage, "(%lu) TEST: WIFI_AP_START_FAILURE_EVENT sent to queue", esp_log_early_timestamp());
            if (xQueueSend(BCQueue, (void*)&msg, portMAX_DELAY) != pdPASS)
            {
                ESP_LOGE("ERROR", "Failed to send WIFI_AP_START_FAILURE_EVENT message to BCQueue");
            }
            vTaskDelay(100 / portTICK_PERIOD_MS);
        }
        else if (testInput == WIFI_CLIENT_CONNECTED)
        {
            msg.eventID = WIFI_CLIENT_CONNECTED;
            sprintf((char*)msg.logMessage, "(%lu) TEST: WIFI_CLIENT_CONNECTED sent to queue", esp_log_early_timestamp());
            if (xQueueSend(BCQueue, (void*)&msg, portMAX_DELAY) != pdPASS)
            {
                ESP_LOGE("ERROR", "Failed to send WIFI_CLIENT_CONNECTED message to BCQueue");
            }
            vTaskDelay(100 / portTICK_PERIOD_MS);
        }
        else if (testInput == WIFI_CLIENT_DISCONNECTED)
        {
            msg.eventID = WIFI_CLIENT_DISCONNECTED;
            sprintf((char*)msg.logMessage, "(%lu) TEST: WIFI_CLIENT_DISCONNECTED sent to queue", esp_log_early_timestamp());
            if (xQueueSend(BCQueue, (void*)&msg, portMAX_DELAY) != pdPASS)
            {
                ESP_LOGE("ERROR", "Failed to send WIFI_CLIENT_DISCONNECTED message to BCQueue");
            }
            vTaskDelay(100 / portTICK_PERIOD_MS);
        }
        else if (testInput == SEC_GSE_AUTH_SUCCESS)
        {
            msg.eventID = SEC_GSE_AUTH_SUCCESS;
            sprintf((char*)msg.logMessage, "(%lu) TEST: SEC_GSE_AUTH_SUCCESS sent to queue", esp_log_early_timestamp());
            if (xQueueSend(BCQueue, (void*)&msg, portMAX_DELAY) != pdPASS)
            {
                ESP_LOGE("ERROR", "Failed to send SEC_GSE_AUTH_SUCCESS message to BCQueue");
            }
            vTaskDelay(100 / portTICK_PERIOD_MS);
        }
        else if (testInput == SEC_IMG_FORMAT_OK)
        {
            msg.eventID = SEC_IMG_FORMAT_OK;
            sprintf((char*)msg.logMessage, "(%lu) TEST: SEC_IMG_FORMAT_OK sent to queue", esp_log_early_timestamp());
            if (xQueueSend(BCQueue, (void*)&msg, portMAX_DELAY) != pdPASS)
            {
                ESP_LOGE("ERROR", "Failed to send SEC_IMG_FORMAT_OK message to BCQueue");
            }
            vTaskDelay(100 / portTICK_PERIOD_MS);
        }
        else if (testInput == SEC_IMG_HASH_OK)
        {
            msg.eventID = SEC_IMG_HASH_OK;
            sprintf((char*)msg.logMessage, "(%lu) TEST: SEC_IMG_HASH_OK sent to queue", esp_log_early_timestamp());
            if (xQueueSend(BCQueue, (void*)&msg, portMAX_DELAY) != pdPASS)
            {
                ESP_LOGE("ERROR", "Failed to send SEC_IMG_HASH_OK message to BCQueue");
            }
            vTaskDelay(100 / portTICK_PERIOD_MS);
        }
        else if (testInput == SEC_IMG_PN_OK)
        {
            msg.eventID = SEC_IMG_PN_OK;
            sprintf((char*)msg.logMessage, "(%lu) TEST: SEC_IMG_PN_OK sent to queue", esp_log_early_timestamp());
            if (xQueueSend(BCQueue, (void*)&msg, portMAX_DELAY) != pdPASS)
            {
                ESP_LOGE("ERROR", "Failed to send SEC_IMG_PN_OK message to BCQueue");
            }
            vTaskDelay(100 / portTICK_PERIOD_MS);
        }
        else
        {
            ESP_LOGW(TAG, "Invalid argument for test command");
        }

        return 0;
    }
    
    ESP_LOGW(TAG, "Too many arguments");

    return 1;

    // ESP_LOGI(TAG, "Test command executed");

    // char recPN[21] = "EMB-HW-002-021-003";
    // char fileName[21] = "EMB-SW-007-137-045";
    // //char recHash[65] = "ebfe440301d71a9a65b095c7d9997c6004058256c0ee22ea0650c30655e48e55";
    // uint8_t recHashBytes[32] = {0xeb, 0xfe, 0x44, 0x03, 0x01, 0xd7, 0x1a, 0x9a,
    //                             0x65, 0xb0, 0x95, 0xc7, 0xd9, 0x99, 0x7c, 0x60,
    //                             0x04, 0x05, 0x82, 0x56, 0xc0, 0xee, 0x22, 0xea,
    //                             0x06, 0x50, 0xc3, 0x06, 0x55, 0xe4, 0x8e, 0x55};

    

    // verify(fileName, recPN, recHashBytes);

}

#endif
