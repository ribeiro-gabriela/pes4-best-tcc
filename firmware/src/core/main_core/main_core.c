#include "main_core.h"

#include "esp_task_wdt.h"

struct tftp_server* server;
TaskHandle_t tftpTaskHandle = NULL;

TaskHandle_t stateTransitionHandle = NULL;

QueueHandle_t BCQueue = NULL;

// Inicializa o core do sistema no estado operacional
void initializeCore()
{
    //Initialize NVS
    esp_err_t ret = nvs_flash_init();
    if (ret == ESP_ERR_NVS_NO_FREE_PAGES || ret == ESP_ERR_NVS_NEW_VERSION_FOUND)
    {
        ESP_ERROR_CHECK(nvs_flash_erase());
        ret = nvs_flash_init();
    }
    ESP_ERROR_CHECK(ret);

    partition_setup();

    init_console();

    bool result;

    result = initializeBCCore();
    if (!result)
    {
        ESP_LOGE("Core Adapter", "Failed to initialize BC Core");
        return;
    }

    result = setBCState(OP_MODE);
    if (!result)
    {
        ESP_LOGE("Core Adapter", "Failed to set BC state to OP_MODE");
        return;
    }
}

void initializeQueue()
{
    if (getBCState() != MNT_MODE)
    {
        // Task para tratar transições de estado e consumir mensagens da fila
        xTaskCreate((void*)stateTransitionHandler, "stateTransitionHandler", 4096, NULL, 5, &stateTransitionHandle);
    }
}

// Inicializa o modo de manutenção com TFTP e WiFi AP
void initializeMaintenanceMode()
{
    if (getBCState() == MNT_MODE)
    {
        wifi_init_softap();

        server = tftp_server_create("/spiffs", 69);
        tftp_server_write_set(server, 1);
        
        // Task para servidor tftp
        xTaskCreate((void*)tftp_server_run, "tftp_server_run", 4096, (void*)server, 5, &tftpTaskHandle);
    }
}

void deinitMaintenanceMode()
{
    if (getBCState() == OP_MODE)
    {
        wifi_deinit_softap();
        tftp_server_destroy(server);

        vTaskSuspend(stateTransitionHandle);
    }
}

void* stateTransitionHandler()
{
    BCQueue = xQueueCreate(10, sizeof(QueueMessage_t));
    if (BCQueue == NULL)
    {
        ESP_LOGE("Core Adapter", "Failed to create BCQueue");
        vTaskDelete(NULL);
    }

    vQueueAddToRegistry(BCQueue, "BCQueue");
    QueueMessage_t receivedMessage;

    while (1)
    {
        if (xQueueReceive(BCQueue, &receivedMessage, 100 / portTICK_PERIOD_MS) == pdPASS)
        {
            // printf("Received message: commandID=%d, stateID=%d, newState=%d\n",
            //     receivedMessage.commandID,
            //     receivedMessage.stateID,
            //     receivedMessage.newState);

            // Tratar do log da mensagem recebida para transição de estado
            if (receivedMessage.eventID == EVENT_ENTER_MAINTENANCE_REQUEST)
            {
                if (getBCState() != MNT_MODE)
                {
                    setBCState(MNT_MODE);
                    printf("Log Message: %s\n", receivedMessage.logMessage);
                    ESP_LOGI("Core Adapter", "BC State changed to MNT_MODE");
                    initializeMaintenanceMode();
                }
            }
            else if (receivedMessage.eventID == EVENT_ABORT_MAINTENANCE_IMMEDIATE)
            {
                if (getBCState() != OP_MODE)
                {
                    setBCState(OP_MODE);
                    printf("Log Message: %s\n", receivedMessage.logMessage);
                    ESP_LOGI("Core Adapter", "BC State changed to OP_MODE");
                    deinitMaintenanceMode();
                }
            }
        }
        // Lógica para tratar mensagens da fila e realizar transições de estado
        vTaskDelay(500 / portTICK_PERIOD_MS);
    }
}
