#include "wifi_adapter.h"
#include "main_core.h"

static const char* TAG = "WiFi";

extern QueueHandle_t BCQueue;

esp_netif_t* netif = NULL;

// [BST-386, BST-387]
void wifiEventHandler(void* arg, esp_event_base_t event_base, int32_t event_id, void* event_data)
{
    QueueMessage_t* msg = (QueueMessage_t*)malloc(sizeof(QueueMessage_t));

    if (event_id == WIFI_EVENT_AP_STACONNECTED)
    {
        wifi_event_ap_staconnected_t* event = (wifi_event_ap_staconnected_t*)event_data;
        ESP_LOGI(TAG, "station " MACSTR " join, AID=%d", MAC2STR(event->mac), event->aid);

        msg->eventID = WIFI_CLIENT_CONNECTED;
        sprintf((char*)msg->logMessage, "(%s) GSE connected", TAG);
        if (xQueueSend(BCQueue, (void*)msg, portMAX_DELAY) != pdPASS)
        {
            ESP_LOGE(TAG, "Failed to send WIFI_CLIENT_CONNECTED message to BCQueue");
        }
    }
    else if (event_id == WIFI_EVENT_AP_STADISCONNECTED)
    {
        wifi_event_ap_stadisconnected_t* event = (wifi_event_ap_stadisconnected_t*)event_data;
        ESP_LOGI(TAG,
                 "station " MACSTR " leave, AID=%d, reason=%d",
                 MAC2STR(event->mac),
                 event->aid,
                 event->reason);

        msg->eventID = WIFI_CLIENT_DISCONNECTED;
        sprintf((char*)msg->logMessage, "(%s) GSE disconnected", TAG);
        if (xQueueSend(BCQueue, (void*)msg, portMAX_DELAY) != pdPASS)
        {
            ESP_LOGE(TAG, "Failed to send WIFI_CLIENT_DISCONNECTED message to BCQueue");
        }
    }

    free(msg);
}

// [BST-380, BST-381, BST-382, BST-383, BST-384, BST-385, BST-388]
void wifiInitSoftAP()
{
    ESP_ERROR_CHECK(esp_netif_init());
    ESP_ERROR_CHECK(esp_event_loop_create_default());
    netif = esp_netif_create_default_wifi_ap();

    wifi_init_config_t cfg = WIFI_INIT_CONFIG_DEFAULT();
    ESP_ERROR_CHECK(esp_wifi_init(&cfg));

    ESP_ERROR_CHECK(esp_event_handler_instance_register(
        WIFI_EVENT, ESP_EVENT_ANY_ID, &wifiEventHandler, NULL, NULL));

    wifi_config_t wifi_config = {
        .ap =
            {
                .ssid = ESP_WIFI_SSID,
                .ssid_len = strlen(ESP_WIFI_SSID),
                .channel = ESP_WIFI_CHANNEL,
                .password = ESP_WIFI_PASS,
                .max_connection = MAX_STA_CONN,
                .authmode = WIFI_AUTH_WPA3_PSK,
                .sae_pwe_h2e = WPA3_SAE_PWE_BOTH,
                .pmf_cfg =
                    {
                        .required = true,
                    },
                .gtk_rekey_interval = EXAMPLE_GTK_REKEY_INTERVAL,
            },
    };
    if (strlen(ESP_WIFI_PASS) == 0)
    {
        wifi_config.ap.authmode = WIFI_AUTH_OPEN;
    }

    ESP_LOGI(TAG, "ESP_WIFI_MODE_AP");

    ESP_ERROR_CHECK(esp_wifi_set_mode(WIFI_MODE_AP));
    ESP_ERROR_CHECK(esp_wifi_set_config(WIFI_IF_AP, &wifi_config));
    esp_err_t res = esp_wifi_start();

    QueueMessage_t* msg = (QueueMessage_t*)malloc(sizeof(QueueMessage_t));
    if (res == ESP_OK)
    {
        ESP_LOGI(TAG,
                 "wifiInitSoftAP finished. SSID: %s password: %s channel: %d",
                 ESP_WIFI_SSID,
                 ESP_WIFI_PASS,
                 ESP_WIFI_CHANNEL);

        msg->eventID = WIFI_AP_STARTED_OK;
        sprintf((char*)msg->logMessage, "(%s) AP started successfully", TAG);
        if (xQueueSend(BCQueue, (void*)msg, portMAX_DELAY) != pdPASS)
        {
            ESP_LOGE(TAG, "Failed to send WIFI_AP_STARTED_OK message to BCQueue");
        }
    }
    else
    {
        msg->eventID = WIFI_AP_START_FAILURE_EVENT;
        sprintf((char*)msg->logMessage, "(%s) AP did not start", TAG);
        if (xQueueSend(BCQueue, (void*)msg, portMAX_DELAY) != pdPASS)
        {
            ESP_LOGE(TAG, "Failed to send WIFI_AP_START_FAILURE_EVENT message to BCQueue");
        }
    }
}

void wifiDeinitSoftAP()
{
    esp_wifi_stop();
    esp_event_loop_delete_default();
    esp_netif_deinit();
    esp_netif_destroy(netif);
    esp_wifi_deinit();

    return;
}
