#include "main_core.h"

#include "esp_task_wdt.h"

struct tftp_server* server;
TaskHandle_t tftpTaskHandle = NULL;

TaskHandle_t stateTransitionHandle = NULL;

QueueHandle_t BCQueue = NULL;

extern int mntSignal;

// Inicializa o core do sistema no estado operacional
void initializeCore()
{
    partitionSetup();
    initLogFile();

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
    QueueMessage_t* msg;

    bool verificationHash = false;
    bool verificationPN = false;
    bool verificationFormat = false;

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
                    mntSignal = false;
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
                    setConnState(RECEIVING_PKTS);
                    printf("Log Message: %s\n", receivedMessage.logMessage);
                    ESP_LOGI("Main Core", "Conn State changed to CRED_EXCHANGE");
                }
            }
            // else if (receivedMessage.eventID == SEC_GSE_AUTH_SUCCESS)
            // {
            //     if (getBCState() == MNT_MODE && getMntState() == CONNECTED && 
            //         getConnState() == CRED_EXCHANGE)
            //     {
            //         setConnState(RECEIVING_PKTS);
            //         printf("Log Message: %s\n", receivedMessage.logMessage);
            //         ESP_LOGI("Main Core", "Conn State changed to RECEIVING_PKTS");
            //     }
            // }
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
                    verificationHash = true;
                }
                else if (receivedMessage.eventID == SEC_IMG_PN_OK && verificationPN == 0)
                {
                    verificationPN = true;
                }
                else if (receivedMessage.eventID == SEC_IMG_FORMAT_OK && verificationFormat == 0)
                {
                    verificationFormat = true;
                }

                if (verificationHash && verificationPN && verificationFormat)
                {
                    if (getBCState() == MNT_MODE && getMntState() == CONNECTED && 
                        getConnState() == IMG_VERIFICATION)
                    {
                        setMntState(WAITING_AUTHORIZATION);
                        setConnState(NOT_SET_CONN);
                        printf("Log Message: %s\n", receivedMessage.logMessage);
                        ESP_LOGI("Main Core", "Image verification successful, Conn State reset to NOT_SET_CONN");
                    }

                    verificationHash = false;
                    verificationPN = false;
                    verificationFormat = false;
                }
            }
            else if (receivedMessage.eventID == SEC_ERR_IMG_HASH_MISMATCH ||
                     receivedMessage.eventID == SEC_ERR_IMG_PN_MISMATCH ||
                     receivedMessage.eventID == SEC_ERR_IMG_BAD_FORMAT)
            {
                // Reset verification flags on any error
                verificationHash = false;
                verificationPN = false;
                verificationFormat = false;

                if (getBCState() == MNT_MODE && getMntState() == CONNECTED && 
                    getConnState() == IMG_VERIFICATION)
                {
                    // Send message according to mismatch to UDP server about verification failure so it can notify GSE

                    setConnState(RECEIVING_PKTS);
                    printf("Log Message: %s\n", receivedMessage.logMessage);
                    ESP_LOGE("Main Core", "Image verification failed");
                }
            }
            else if (receivedMessage.eventID == COMM_AUTH_FAILURE ||
                     receivedMessage.eventID == COMM_TIMEOUT)
            {
                if (getBCState() == MNT_MODE && getMntState() == CONNECTED)
                {
                    setMntState(WAITING);
                    setConnState(NOT_SET_CONN);
                    printf("Log Message: %s\n", receivedMessage.logMessage);
                    ESP_LOGI("Main Core", "MNT State changed to WAITING due to communication failure");
                }
            }
            else if (receivedMessage.eventID == CORE_WARN_UNEXPECTED_EVENT)
            {
                printf("Log Message: %s\n", receivedMessage.logMessage);
                ESP_LOGW("Main Core", "Received unexpected event");
            }
            else if (receivedMessage.eventID == LOG_INFO)
            {
                printf("Log Message: %s\n", receivedMessage.logMessage);
                ESP_LOGI("Main Core", "Info log received");
            }
            else if (receivedMessage.eventID == ERR_GSE_PROBE_TIMEOUT)
            {
                printf("Log Message: %s\n", receivedMessage.logMessage);
                ESP_LOGE("Main Core", "GSE probe timeout error");
            }
            else if (receivedMessage.eventID == ERR_AP_INIT_FAILED)
            {
                printf("Log Message: %s\n", receivedMessage.logMessage);
                ESP_LOGE("Main Core", "Access Point initialization failed");
                setBCState(OP_MODE);
                setMntState(NOT_SET_MNT);
                setConnState(NOT_SET_CONN);
                deinitMaintenanceMode();
                msg = (QueueMessage_t*) malloc(sizeof(QueueMessage_t));
                if (msg != NULL)
                {
                    msg->eventID = EVENT_ENTER_MAINTENANCE_REQUEST;
                    sprintf((char*)msg->logMessage, "%lu: WiFi AP failed to start due to AP init failure", esp_log_early_timestamp());
                    if (xQueueSend(BCQueue, (void*) msg, portMAX_DELAY) != pdPASS)
                    {
                        ESP_LOGE("Main Core", "Failed to send message to BCQueue");
                    }
                    free(msg);
                }
            }
            else if (receivedMessage.eventID == EVENT_SENSORS_LINK_DOWN)
            {
                printf("Log Message: %s\n", receivedMessage.logMessage);
                ESP_LOGE("Main Core", "Sensors link down event");
                
                msg = (QueueMessage_t*) malloc(sizeof(QueueMessage_t));
                if (msg != NULL)
                {
                    msg->eventID = EVENT_ABORT_MAINTENANCE_IMMEDIATE;
                    sprintf((char*)msg->logMessage, "%lu: Sensors link down, aborting maintenance mode", esp_log_early_timestamp());
                    if (xQueueSend(BCQueue, (void*) msg, portMAX_DELAY) != pdPASS)
                    {
                        ESP_LOGE("Main Core", "Failed to send message to BCQueue");
                    }
                    free(msg);
                }
            }
            else if (receivedMessage.eventID == SEC_ERR_GSE_AUTH_FAILED)
            {
                printf("Log Message: %s\n", receivedMessage.logMessage);
                ESP_LOGE("Main Core", "GSE authentication failed");
                if (getBCState() == MNT_MODE)
                {
                    setMntState(WAITING);
                    setConnState(NOT_SET_CONN);
                    ESP_LOGI("Main Core", "MNT State changed to WAITING due to GSE auth failure");
                }
            }
            else if (receivedMessage.eventID == WIFI_AP_STARTED_OK)
            {
                printf("Log Message: %s\n", receivedMessage.logMessage);
                ESP_LOGI("Main Core", "WiFi AP started successfully");
            }
            else if (receivedMessage.eventID == WIFI_AP_START_FAILURE_EVENT)
            {
                printf("Log Message: %s\n", receivedMessage.logMessage);
                ESP_LOGE("Main Core", "WiFi AP failed to start");
                setBCState(OP_MODE);
                setMntState(NOT_SET_MNT);
                setConnState(NOT_SET_CONN);
                deinitMaintenanceMode();
                msg = (QueueMessage_t*) malloc(sizeof(QueueMessage_t));
                if (msg != NULL)
                {
                    msg->eventID = EVENT_ENTER_MAINTENANCE_REQUEST;
                    sprintf((char*)msg->logMessage, "%lu: WiFi AP failed to start", esp_log_early_timestamp());
                    if (xQueueSend(BCQueue, (void*) msg, portMAX_DELAY) != pdPASS)
                    {
                        ESP_LOGE("Main Core", "Failed to send message to BCQueue");
                    }
                    free(msg);
                }
            }
        }
        //vTaskDelay(500 / portTICK_PERIOD_MS);
    }
}
