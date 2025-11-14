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

    partitionSetup();

    initConsole();

    bool result;

    result = initializeBCCore();
    if (!result)
    {
        ESP_LOGE("Main Core", "Failed to initialize BC Core");
        return;
    }

    result = setBCState(OP_MODE);
    if (!result)
    {
        ESP_LOGE("Main Core", "Failed to set BC state to OP_MODE");
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
        wifiInitSoftAP();

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
        wifiDeinitSoftAP();
        tftp_server_destroy(server);

        vTaskSuspend(stateTransitionHandle);
    }
}

void* stateTransitionHandler()
{
    // Verificar se a fila tem o tamanho correto, podemos reduzir o tamanho da fila se necessário
    BCQueue = xQueueCreate(10, sizeof(QueueMessage_t));
    if (BCQueue == NULL)
    {
        ESP_LOGE("Main Core", "Failed to create BCQueue");
        vTaskDelete(NULL);
    }

    vQueueAddToRegistry(BCQueue, "BCQueue");
    QueueMessage_t receivedMessage;

    int verificationHash = 0;
    int verificationPN = 0;
    int verificationFormat = 0;

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
                    setMntState(WAITING);
                    printf("Log Message: %s\n", receivedMessage.logMessage);
                    ESP_LOGI("Main Core", "BC State changed to MNT_MODE");
                    initializeMaintenanceMode();
                }
            }
            else if (receivedMessage.eventID == EVENT_ABORT_MAINTENANCE_IMMEDIATE)
            {
                if (getBCState() != OP_MODE)
                {
                    setBCState(OP_MODE);
                    setMntState(NOT_SET_MNT);
                    setConnState(NOT_SET_CONN);
                    printf("Log Message: %s\n", receivedMessage.logMessage);
                    ESP_LOGI("Main Core", "BC State changed to OP_MODE");
                    deinitMaintenanceMode();
                }
            }
            else if (receivedMessage.eventID == WIFI_CLIENT_CONNECTED)
            {
                if (getBCState() == MNT_MODE && getMntState() == WAITING)
                {
                    setMntState(CONNECTED);
                    setConnState(WAITING_REQUEST);
                    printf("Log Message: %s\n", receivedMessage.logMessage);
                    ESP_LOGI("Main Core", "MNT State changed to CONNECTED");
                }
            }
            else if (receivedMessage.eventID == WIFI_CLIENT_DISCONNECTED ||
                     receivedMessage.eventID == COMM_AUTH_FAILURE)
            {
                if (getBCState() == MNT_MODE && getMntState() == CONNECTED)
                {
                    setMntState(WAITING);
                    setConnState(NOT_SET_CONN);
                    printf("Log Message: %s\n", receivedMessage.logMessage);
                    ESP_LOGI("Main Core", "MNT State changed to WAITING");
                }
            }
            else if (receivedMessage.eventID == LOAD_REQUEST)
            {
                if (getBCState() == MNT_MODE && getMntState() == CONNECTED && 
                    getConnState() == WAITING_REQUEST)
                {
                    setConnState(CRED_EXCHANGE);
                    printf("Log Message: %s\n", receivedMessage.logMessage);
                    ESP_LOGI("Main Core", "Conn State changed to CRED_EXCHANGE");
                }
            }
            else if (receivedMessage.eventID == SEC_GSE_AUTH_SUCCESS)
            {
                if (getBCState() == MNT_MODE && getMntState() == CONNECTED && 
                    getConnState() == CRED_EXCHANGE)
                {
                    setConnState(RECEIVING_PKTS);
                    printf("Log Message: %s\n", receivedMessage.logMessage);
                    ESP_LOGI("Main Core", "Conn State changed to RECEIVING_PKTS");
                }
            }
            else if (receivedMessage.eventID == COMM_TRANSFER_COMPLETE)
            {
                if (getBCState() == MNT_MODE && getMntState() == CONNECTED && 
                    getConnState() == RECEIVING_PKTS)
                {
                    setConnState(IMG_VERIFICATION);
                    printf("Log Message: %s\n", receivedMessage.logMessage);
                    ESP_LOGI("Main Core", "Conn State changed to IMG_VERIFICATION");
                }
            }
            else if (receivedMessage.eventID == SEC_IMG_HASH_OK ||
                     receivedMessage.eventID == SEC_IMG_PN_OK ||
                     receivedMessage.eventID == SEC_IMG_FORMAT_OK)
            {
                if (receivedMessage.eventID == SEC_IMG_HASH_OK && verificationHash == 0)
                {
                    verificationHash = 1;
                }
                else if (receivedMessage.eventID == SEC_IMG_PN_OK && verificationPN == 0)
                {
                    verificationPN = 1;
                }
                else if (receivedMessage.eventID == SEC_IMG_FORMAT_OK && verificationFormat == 0)
                {
                    verificationFormat = 1;
                }

                if (verificationHash == 1 && verificationPN == 1 && verificationFormat == 1)
                {
                    if (getBCState() == MNT_MODE && getMntState() == CONNECTED && 
                        getConnState() == IMG_VERIFICATION)
                    {
                        setMntState(WAITING_AUTHORIZATION);
                        setConnState(NOT_SET_CONN);
                        printf("Log Message: %s\n", receivedMessage.logMessage);
                        ESP_LOGI("Main Core", "Image verification successful, Conn State reset to NOT_SET_CONN");
                    }

                    verificationHash = 0;
                    verificationPN = 0;
                    verificationFormat = 0;
                }
            }
            else if (receivedMessage.eventID == SEC_ERR_IMG_HASH_MISMATCH ||
                     receivedMessage.eventID == SEC_ERR_IMG_PN_MISMATCH ||
                     receivedMessage.eventID == SEC_ERR_IMG_BAD_FORMAT)
            {
                // Reset verification flags on any error
                verificationHash = 0;
                verificationPN = 0;
                verificationFormat = 0;

                if (getBCState() == MNT_MODE && getMntState() == CONNECTED && 
                    getConnState() == IMG_VERIFICATION)
                {
                    setConnState(RECEIVING_PKTS);
                    printf("Log Message: %s\n", receivedMessage.logMessage);
                    ESP_LOGE("Main Core", "Image verification failed");
                }
            }
        }
        //vTaskDelay(500 / portTICK_PERIOD_MS);
    }
}
