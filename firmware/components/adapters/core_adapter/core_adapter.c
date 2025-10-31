#include "core_adapter.h"

#include "esp_task_wdt.h"

struct tftp_server* server;
TaskHandle_t tftpTaskHandle = NULL;

TaskHandle_t stateTransitionHandle = NULL;

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

// Inicializa o modo de manutenção com TFTP e WiFi AP
void initializeMaintenanceMode()
{
    if (getBCState() != MNT_MODE)
    {
        wifi_init_softap();

        server = tftp_server_create("/spiffs", 69);
        tftp_server_write_set(server, 1);
        
        // Task para servidor tftp
        xTaskCreate((void*)tftp_server_run, "tftp_server_run", 4096, (void*)server, 5, &tftpTaskHandle);

        // Task para tratar transições de estado e consumir mensagens da fila
        xTaskCreate((void*)stateTransitionHandler, "stateTransitionHandler", 4096, NULL, 5, &stateTransitionHandle);
        // Removendo a task do watchdog, pois ainda não há tratamento adequado
        esp_task_wdt_delete(stateTransitionHandle);

        bool result = setBCState(MNT_MODE);
        if (!result)
        {
            ESP_LOGE("Core Adapter", "Failed to set BC state to MNT_MODE");
            return;
        }
    }
}

void deinitMaintenanceMode()
{
    if (getBCState() == MNT_MODE)
    {
        wifi_deinit_softap();
        tftp_server_destroy(server);

        bool result = setBCState(OP_MODE);
        if (!result)
        {
            ESP_LOGE("Core Adapter", "Failed to set BC state to OP_MODE");
            return;
        }
        vTaskDelete(stateTransitionHandle);
    }
}

void* stateTransitionHandler()
{
    QueueHandle_t BCQueue = xQueueCreate(10, sizeof(QueueMessage_t));
    if (BCQueue == NULL)
    {
        ESP_LOGE("Core Adapter", "Failed to create BCQueue");
        vTaskDelete(NULL);
    }

    vQueueAddToRegistry(BCQueue, "BCQueue");

    while (1)
    {
        // Lógica para tratar mensagens da fila e realizar transições de estado
        vTaskDelay(1000 / portTICK_PERIOD_MS);
    }
}