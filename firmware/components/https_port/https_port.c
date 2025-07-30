#include <stdio.h>
#include "https_port.h"

#define CONFIG_ESP_TLS_USING_MBEDTLS

extern const uint8_t server_cert_pem_start[] asm("_binary_server_cert_pem_start");
extern const uint8_t server_cert_pem_end[] asm("_binary_server_cert_pem_end");
extern const uint8_t server_key_pem_start[] asm("_binary_server_key_pem_start");
extern const uint8_t server_key_pem_end[] asm("_binary_server_key_pem_end");

static const char* TAG = "HTTPS";

esp_err_t get_hello_handler(httpd_req_t* request)
{
    char* msg = "Hello World!";

    httpd_resp_send(request, msg, HTTPD_RESP_USE_STRLEN);

    return ESP_OK;
}

httpd_uri_t get_hello = {
    .uri = "/",
    .method = HTTP_GET,
    .handler = get_hello_handler,
    .user_ctx = NULL
};

void https_event_handler(void* arg, esp_event_base_t event_base, 
                        int32_t event_id, void* event_data)
{
    if (event_base == ESP_HTTPS_SERVER_EVENT) {
        if (event_id == HTTPS_SERVER_EVENT_ERROR) {
            esp_https_server_last_error_t *last_error = (esp_tls_last_error_t *) event_data;
            ESP_LOGE(TAG, "Error event triggered: last_error = %s, last_tls_err = %d, tls_flag = %d", esp_err_to_name(last_error->last_error), last_error->esp_tls_error_code, last_error->esp_tls_flags);
        }
    }
}                        

httpd_handle_t start_webserver()
{
    httpd_handle_t server = NULL;
    httpd_ssl_config_t ssl_config = HTTPD_SSL_CONFIG_DEFAULT();

    ssl_config.servercert = server_cert_pem_start;
    ssl_config.servercert_len = server_cert_pem_end - server_cert_pem_start;
    ssl_config.prvtkey_pem = server_key_pem_start;
    ssl_config.prvtkey_len = server_key_pem_end - server_key_pem_start;

    //ssl_config.user_cb = https_server_user_callback;

    esp_err_t status = httpd_ssl_start(&server, &ssl_config);

    if (status != ESP_OK)
    {
        ESP_LOGE(TAG, "Error starting server!");
        return NULL;
    }

    httpd_register_uri_handler(server, &get_hello);

    ESP_LOGI(TAG, "Server started successfully!");

    return server;
}                        

void init_https_server()
{
    ESP_ERROR_CHECK(esp_event_handler_register(ESP_HTTPS_SERVER_EVENT, 
                                               ESP_EVENT_ANY_ID, 
                                               &https_event_handler, NULL));

    httpd_handle_t server = start_webserver();
}
