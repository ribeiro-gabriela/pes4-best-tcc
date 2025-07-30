#include <stdio.h>
#include "https_port.h"

#define CONFIG_ESP_TLS_USING_MBEDTLS

extern const uint8_t server_cert_pem_start[] asm("_binary_server_cert_pem_start");
extern const uint8_t server_cert_pem_end[] asm("_binary_server_cert_pem_end");
extern const uint8_t server_key_pem_start[] asm("_binary_server_key_pem_start");
extern const uint8_t server_key_pem_end[] asm("_binary_server_key_pem_end");

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

static const char* TAG = "HTTPS";

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

// static void connect_handler(void* arg, esp_event_base_t event_base, 
//                             int32_t event_id, void* event_data)
// {
//     httpd_handle_t* server = (httpd_handle_t*) arg;

//     if (*server == NULL)
//     {
//         *server = start_webserver();
//     }
// }                            

void init_https_server()
{
    ESP_ERROR_CHECK(esp_event_handler_register(ESP_HTTPS_SERVER_EVENT, ESP_EVENT_ANY_ID, &https_event_handler, NULL));

    httpd_handle_t server = start_webserver();
}

// void https_server_user_callback(esp_https_server_user_cb_arg_t *user_cb)
// {
//     ESP_LOGI(TAG, "User callback invoked!");
// #ifdef CONFIG_ESP_TLS_USING_MBEDTLS
//     mbedtls_ssl_context *ssl_ctx = NULL;
// #endif
//     switch(user_cb->user_cb_state) {
//         case HTTPD_SSL_USER_CB_SESS_CREATE:
//             ESP_LOGD(TAG, "At session creation");

//             // Logging the socket FD
//             int sockfd = -1;
//             esp_err_t esp_ret;
//             esp_ret = esp_tls_get_conn_sockfd(user_cb->tls, &sockfd);
//             if (esp_ret != ESP_OK) {
//                 ESP_LOGE(TAG, "Error in obtaining the sockfd from tls context");
//                 break;
//             }
//             ESP_LOGI(TAG, "Socket FD: %d", sockfd);
// #ifdef CONFIG_ESP_TLS_USING_MBEDTLS
//             ssl_ctx = (mbedtls_ssl_context *) esp_tls_get_ssl_context(user_cb->tls);
//             if (ssl_ctx == NULL) {
//                 ESP_LOGE(TAG, "Error in obtaining ssl context");
//                 break;
//             }
//             // Logging the current ciphersuite
//             ESP_LOGI(TAG, "Current Ciphersuite: %s", mbedtls_ssl_get_ciphersuite(ssl_ctx));
// #endif
//             break;

//         case HTTPD_SSL_USER_CB_SESS_CLOSE:
//             ESP_LOGD(TAG, "At session close");
// #ifdef CONFIG_ESP_TLS_USING_MBEDTLS
//             // Logging the peer certificate
//             ssl_ctx = (mbedtls_ssl_context *) esp_tls_get_ssl_context(user_cb->tls);
//             if (ssl_ctx == NULL) {
//                 ESP_LOGE(TAG, "Error in obtaining ssl context");
//                 break;
//             }
//             //print_peer_cert_info(ssl_ctx);
// #endif
//             break;
//         default:
//             ESP_LOGE(TAG, "Illegal state!");
//             return;
//     }
// }
