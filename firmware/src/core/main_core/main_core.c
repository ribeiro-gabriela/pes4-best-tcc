#include "main_core.h"

TaskHandle_t stateTransitionHandle = NULL;
TaskHandle_t sensorHandle = NULL;

QueueHandle_t BCQueue = NULL;

extern sensorData_t sensors;

// BST-475
void initializeCore()
{
    storageInit();

    cliInit();

    initializeQueue();

    initSensorPolling();

    bool result;

    result = initializeFSM();
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

void initSensorPolling()
{
    if (getBCState() != MNT_MODE)
    {
        xTaskCreate((void*)sensorPolling, "sensorPolling", 4096, NULL, 5, &sensorHandle);
    }
}

// BST-608
void* sensorPolling()
{
    sensorData_t prevValues = sensors;
    QueueMessage_t* msg = (QueueMessage_t*) malloc(sizeof(QueueMessage_t));

    while (1)
    {
        if (sensors.mntSignal != prevValues.mntSignal || 
            sensors.parkingBrake != prevValues.parkingBrake || 
            sensors.weightOnWheels != prevValues.weightOnWheels)
        {
            if (sensors.mntSignal && sensors.parkingBrake && sensors.weightOnWheels)
            {
                if (getBCState() != MNT_MODE)
                {
                    ESP_LOGI("Sensors", "All conditions met for maintenance mode. Enabling maintenance mode.");
                    
                    msg->eventID = EVENT_ENTER_MAINTENANCE_REQUEST;
                    sprintf((char*)msg->logMessage, "%lu: Maintenance mode enabled via sensor conditions", esp_log_early_timestamp());

                    if (xQueueSend(BCQueue, (void*) msg, portMAX_DELAY) != pdPASS)
                    {
                        ESP_LOGE("Sensors", "Failed to send message to BCQueue");
                    }
                }
            }
            else
            {
                if (getBCState() != OP_MODE)
                {
                    ESP_LOGI("Sensors", "Conditions not met for maintenance mode. Disabling maintenance mode.");

                    msg->eventID = EVENT_ABORT_MAINTENANCE_IMMEDIATE;
                    sprintf((char*)msg->logMessage, "%lu: Maintenance mode disabled via sensor conditions", esp_log_early_timestamp());

                    if (xQueueSend(BCQueue, (void*) msg, portMAX_DELAY) != pdPASS)
                    {
                        ESP_LOGE("Sensors", "Failed to send message to BCQueue");
                    }
                }
            }

            prevValues = sensors;
        }

        vTaskDelay(10 / portTICK_PERIOD_MS);
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
        commInit();
    }
}

void deinitMaintenanceMode()
{
    if (getBCState() == OP_MODE)
    {
        commDeinit();

        //vTaskSuspend(stateTransitionHandle);
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
            if (receivedMessage.eventID == EVENT_ENTER_MAINTENANCE_REQUEST)
            {
                if (getBCState() != MNT_MODE)
                {
                    setBCState(MNT_MODE);
                    setMntState(WAITING);
                    ESP_LOGI("LOG_INFO", "Log Message: %s\n", receivedMessage.logMessage);
                    ESP_LOGI("Main Core", "BC State changed to MNT_MODE");
                    initializeMaintenanceMode();
                }
                else
                {
                    if (!sensors.mntSignal || !sensors.parkingBrake || !sensors.weightOnWheels)
                    {
                        ESP_LOGW("Main Core", "Cannot enter maintenance mode, sensor conditions not met");
                    }
                    else
                    {
                        ESP_LOGW("Main Core", "Received EVENT_ENTER_MAINTENANCE_REQUEST event in unexpected state, ignoring");
                    }
                }
            }
            else if (receivedMessage.eventID == EVENT_ABORT_MAINTENANCE_IMMEDIATE)
            {
                if (getBCState() != OP_MODE)
                {
                    sensors.mntSignal = false;
                    setBCState(OP_MODE);
                    setMntState(NOT_SET_MNT);
                    setConnState(NOT_SET_CONN);
                    ESP_LOGI("LOG_INFO", "Log Message: %s\n", receivedMessage.logMessage);
                    ESP_LOGI("Main Core", "BC State changed to OP_MODE");
                    deinitMaintenanceMode();
                }
                else
                {
                    ESP_LOGW("Main Core", "Received EVENT_ABORT_MAINTENANCE_IMMEDIATE event in unexpected state, ignoring");
                }
            }
            else if (receivedMessage.eventID == WIFI_CLIENT_CONNECTED)
            {
                if (getBCState() == MNT_MODE && getMntState() == WAITING)
                {
                    setMntState(CONNECTED);
                    setConnState(WAITING_REQUEST);
                    ESP_LOGI("LOG_INFO", "Log Message: %s\n", receivedMessage.logMessage);
                    ESP_LOGI("Main Core", "MNT State changed to CONNECTED and Conn State changed to WAITING_REQUEST");
                }
                else
                {
                    ESP_LOGW("Main Core", "Received WIFI_CLIENT_CONNECTED event in unexpected state, ignoring");
                }
            }
            else if (receivedMessage.eventID == WIFI_CLIENT_DISCONNECTED ||
                     receivedMessage.eventID == COMM_AUTH_FAILURE)
            {
                if (getBCState() == MNT_MODE && getMntState() == CONNECTED)
                {
                    setMntState(WAITING);
                    setConnState(NOT_SET_CONN);
                    ESP_LOGI("LOG_INFO", "Log Message: %s\n", receivedMessage.logMessage);
                    ESP_LOGI("Main Core", "MNT State changed to WAITING");
                }
                else
                {
                    if (receivedMessage.eventID == WIFI_CLIENT_DISCONNECTED)
                    {
                        ESP_LOGW("Main Core", "Received WIFI_CLIENT_DISCONNECTED event in unexpected state, ignoring");
                    }
                    else if (receivedMessage.eventID == COMM_AUTH_FAILURE)
                    {
                        ESP_LOGW("Main Core", "Received COMM_AUTH_FAILURE event in unexpected state, ignoring");
                    }
                }
            }
            else if (receivedMessage.eventID == LOAD_REQUEST)
            {
                if (getBCState() == MNT_MODE && getMntState() == CONNECTED && 
                    getConnState() == WAITING_REQUEST)
                {
                    setConnState(RECEIVING_PKTS);
                    ESP_LOGI("LOG_INFO", "Log Message: %s\n", receivedMessage.logMessage);
                    ESP_LOGI("Main Core", "Conn State changed to RECEIVING_PKTS");
                }
                else
                {
                    ESP_LOGW("Main Core", "Received LOAD_REQUEST event in unexpected state, ignoring");
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
                    ESP_LOGI("LOG_INFO", "Log Message: %s\n", receivedMessage.logMessage);
                    ESP_LOGI("Main Core", "Conn State changed to IMG_VERIFICATION");

                    #define TEST_COMMAND_ENABLED
                    #ifdef TEST_COMMAND_ENABLED

                    FILE* recHeaderFile = fopen("/spiffs/test_file.bin", "rb");
                    if (recHeaderFile == NULL)
                    {
                        ESP_LOGE("Main Core", "Failed to open received header file for reading");
                        continue;
                    }
                    else
                    {
                        char recSWPN[21], recHWPN[21];
                        uint8_t recHash[32];

                        for (size_t i = 0; i < 20; i++)
                        {
                            recSWPN[i] = (char)fgetc(recHeaderFile);
                        }
                        recSWPN[20] = '\0';
                        for (size_t i = 0; i < 20; i++)
                        {
                            recHWPN[i] = (char)fgetc(recHeaderFile);
                        }
                        recHWPN[20] = '\0';
                        for (size_t i = 0; i < 32; i++)
                        {
                            recHash[i] = (uint8_t)fgetc(recHeaderFile);
                        }

                        fclose(recHeaderFile);

                        verify(recSWPN, recHWPN, recHash);
                    }

                    #endif

                }
                else
                {
                    ESP_LOGW("Main Core", "Received COMM_TRANSFER_COMPLETE event in unexpected state, ignoring");
                }
            }
            else if (receivedMessage.eventID == SEC_IMG_HASH_OK ||
                     receivedMessage.eventID == SEC_IMG_PN_OK ||
                     receivedMessage.eventID == SEC_IMG_FORMAT_OK)
            {
                if (receivedMessage.eventID == SEC_IMG_HASH_OK && !verificationHash)
                {
                    verificationHash = true;
                }
                else if (receivedMessage.eventID == SEC_IMG_PN_OK && !verificationPN)
                {
                    verificationPN = true;
                }
                else if (receivedMessage.eventID == SEC_IMG_FORMAT_OK && !verificationFormat)
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
                        ESP_LOGI("LOG_INFO", "Log Message: %s\n", receivedMessage.logMessage);
                        ESP_LOGI("Main Core", "MNT State changed to WAITING_AUTHORIZATION");
                    }
                    else
                    {
                        ESP_LOGW("Main Core", "Received image verification success events in unexpected state, ignoring");
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
                    ESP_LOGI("LOG_INFO", "Log Message: %s\n", receivedMessage.logMessage);
                    ESP_LOGE("Main Core", "Conn State reverted to RECEIVING_PKTS");
                }
                else
                {
                    ESP_LOGW("Main Core", "Received image verification error event in unexpected state, ignoring");
                }
            }
            else if (receivedMessage.eventID == COMM_AUTH_FAILURE ||
                     receivedMessage.eventID == COMM_TIMEOUT)
            {
                if (getBCState() == MNT_MODE && getMntState() == CONNECTED)
                {
                    setMntState(WAITING);
                    setConnState(NOT_SET_CONN);
                    ESP_LOGI("LOG_INFO", "Log Message: %s\n", receivedMessage.logMessage);
                    ESP_LOGI("Main Core", "MNT State changed to WAITING");
                }
                else
                {
                    if (receivedMessage.eventID == COMM_AUTH_FAILURE)
                    {
                        ESP_LOGW("Main Core", "Received COMM_AUTH_FAILURE event in unexpected state, ignoring");
                    }
                    else
                    {
                        ESP_LOGW("Main Core", "Received COMM_TIMEOUT event in unexpected state, ignoring");
                    }
                }
            }
            else if (receivedMessage.eventID == CORE_WARN_UNEXPECTED_EVENT)
            {
                ESP_LOGI("LOG_INFO", "Log Message: %s\n", receivedMessage.logMessage);
                ESP_LOGW("Main Core", "Received unexpected event");
            }
            else if (receivedMessage.eventID == LOG_INFO)
            {
                ESP_LOGI("Main Core", "Info log received");
                ESP_LOGI("LOG_INFO", "Log Message: %s\n", receivedMessage.logMessage);
            }
            else if (receivedMessage.eventID == ERR_GSE_PROBE_TIMEOUT)
            {
                ESP_LOGI("LOG_INFO", "Log Message: %s\n", receivedMessage.logMessage);
                ESP_LOGE("Main Core", "GSE probe timeout exceeded, aborting maintenance mode");
                setBCState(OP_MODE);
                setMntState(NOT_SET_MNT);
                setConnState(NOT_SET_CONN);
                deinitMaintenanceMode();
            }
            else if (receivedMessage.eventID == ERR_AP_INIT_FAILED)
            {
                ESP_LOGI("LOG_INFO", "Log Message: %s\n", receivedMessage.logMessage);
                ESP_LOGE("Main Core", "Access Point initialization failed, reinitializing Maintenance Mode");
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
                ESP_LOGI("LOG_INFO", "Log Message: %s\n", receivedMessage.logMessage);
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
                ESP_LOGI("LOG_INFO", "Log Message: %s\n", receivedMessage.logMessage);
                ESP_LOGE("Main Core", "GSE authentication failed");
                if (getBCState() == MNT_MODE)
                {
                    setMntState(WAITING);
                    setConnState(NOT_SET_CONN);
                    ESP_LOGI("Main Core", "MNT State changed to WAITING due to GSE auth failure");
                }
                else
                {
                    ESP_LOGW("Main Core", "Received SEC_ERR_GSE_AUTH_FAILED event in unexpected state, ignoring");
                }
            }
            else if (receivedMessage.eventID == WIFI_AP_STARTED_OK)
            {
                if (getBCState() == MNT_MODE && getMntState() == WAITING)
                {
                    ESP_LOGI("LOG_INFO", "Log Message: %s\n", receivedMessage.logMessage);
                    ESP_LOGI("Main Core", "WiFi AP started successfully");
                }
                else
                {
                    ESP_LOGW("Main Core", "Received WIFI_AP_STARTED_OK event in unexpected state, ignoring");
                }
            }
            else if (receivedMessage.eventID == WIFI_AP_START_FAILURE_EVENT)
            {
                if (getBCState() == MNT_MODE && getMntState() == WAITING)
                {
                    ESP_LOGI("LOG_INFO", "Log Message: %s\n", receivedMessage.logMessage);
                    ESP_LOGE("Main Core", "WiFi AP failed to start, reinitializing Maintenance Mode");
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
                else
                {
                    ESP_LOGW("Main Core", "Received WIFI_AP_START_FAILURE_EVENT event in unexpected state, ignoring");
                }
            }
        }
        vTaskDelay(3000 / portTICK_PERIOD_MS);
    }
}
