#include <stdio.h>
#include "https_port.h"

#ifndef MIN
#define MIN(a, b) ((a) < (b) ? (a) : (b))
#endif

extern const uint8_t server_cert_pem_start[] asm("_binary_server_cert_pem_start");
extern const uint8_t server_cert_pem_end[] asm("_binary_server_cert_pem_end");
extern const uint8_t server_key_pem_start[] asm("_binary_server_key_pem_start");
extern const uint8_t server_key_pem_end[] asm("_binary_server_key_pem_end");

static const char* TAG = "HTTPS";

esp_err_t get_bc_status_handler(httpd_req_t* request) {
    char* msg = "ready";

    httpd_resp_set_type(request, "text/plain");

    httpd_resp_send(request, msg, HTTPD_RESP_USE_STRLEN);

    return ESP_OK;
}

esp_err_t post_file_handler(httpd_req_t* request) {
    const char* filepath = "/spiffs/gabi.txt";

    FILE* file = fopen(filepath, "w");

    if (!file)
    {
        perror("fopen");
        ESP_LOGE(TAG, "could not create file");
        httpd_resp_send_err(request, HTTPD_500_INTERNAL_SERVER_ERROR, "internal error");
        return ESP_FAIL;
    }

    int total_len = request->content_len;
    int cur_len = 0;
    int received = 0;
    char buf[128];

    while (cur_len < total_len)
    {
        received = httpd_req_recv(request, buf, MIN(sizeof(buf), total_len - cur_len));
        if (received <= 0) {
            fclose(file);
            ESP_LOGE(TAG, "could not receive file");
            httpd_resp_send_err(request, HTTPD_500_INTERNAL_SERVER_ERROR, "internal error");
            return ESP_FAIL;
        }

        fwrite(buf, 1, received, file);
        cur_len += received;
    }

    fclose(file);

    const char* resp = "file received";
    httpd_resp_send(request, resp, strlen(resp));
    return ESP_OK;
}

esp_err_t get_bc_info_handler(httpd_req_t* request)
{
    const char* filepath = "/spiffs/EMB-0001-021-045.txt";

    FILE* file = fopen(filepath, "r");

    if(!file)
    {
        const char* err = "internal error";

        httpd_resp_send_500(request);
        return ESP_FAIL;
    }    

    httpd_resp_set_type(request, "text/plain");

    char line[128];
    while (fgets(line, sizeof(line), file)) {
        httpd_resp_send_chunk(request, line, strlen(line));
    }

    fclose(file);
    httpd_resp_send_chunk(request, NULL, 0); // Finaliza chunked response

    return ESP_OK;
}

httpd_uri_t get_bc_status = {
    .uri = "/status",
    .method = HTTP_GET,
    .handler = get_bc_status_handler,
    .user_ctx = NULL
};

httpd_uri_t get_bc_info = {
    .uri = "/info",
    .method = HTTP_GET,
    .handler = get_bc_info_handler,
    .user_ctx = NULL
};

httpd_uri_t post_file = {
    .uri = "/file",
    .method = HTTP_POST,
    .handler = post_file_handler,
    .user_ctx = NULL
};


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

    ssl_config.user_cb = https_server_user_callback;

    esp_err_t status = httpd_ssl_start(&server, &ssl_config);

    if (status != ESP_OK)
    {
        ESP_LOGE(TAG, "Error starting server!");
        return NULL;
    }

    httpd_register_uri_handler(server, &get_hello);
    httpd_register_uri_handler(server, &get_bc_info);
    httpd_register_uri_handler(server, &get_bc_status);
    httpd_register_uri_handler(server, &post_file);

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

static void https_server_user_callback(esp_https_server_user_cb_arg_t *user_cb)
{
    ESP_LOGI(TAG, "User callback invoked!");
    mbedtls_ssl_context *ssl_ctx = NULL;

    switch(user_cb->user_cb_state) {
        case HTTPD_SSL_USER_CB_SESS_CREATE:
            ESP_LOGD(TAG, "At session creation");

            // Logging the socket FD
            int sockfd = -1;
            esp_err_t esp_ret;
            esp_ret = esp_tls_get_conn_sockfd(user_cb->tls, &sockfd);
            if (esp_ret != ESP_OK) {
                ESP_LOGE(TAG, "Error in obtaining the sockfd from tls context");
                break;
            }
            ESP_LOGI(TAG, "Socket FD: %d", sockfd);
            ssl_ctx = (mbedtls_ssl_context *) esp_tls_get_ssl_context(user_cb->tls);
            if (ssl_ctx == NULL) {
                ESP_LOGE(TAG, "Error in obtaining ssl context");
                break;
            }
            // Logging the current ciphersuite
            ESP_LOGI(TAG, "Current Ciphersuite: %s", mbedtls_ssl_get_ciphersuite(ssl_ctx));
            break;

        case HTTPD_SSL_USER_CB_SESS_CLOSE:
            ESP_LOGD(TAG, "At session close");
            // Logging the peer certificate
            ssl_ctx = (mbedtls_ssl_context *) esp_tls_get_ssl_context(user_cb->tls);
            if (ssl_ctx == NULL) {
                ESP_LOGE(TAG, "Error in obtaining ssl context");
                break;
            }
            print_peer_cert_info(ssl_ctx);
            break;
        default:
            ESP_LOGE(TAG, "Illegal state!");
            return;
    }
}

static void print_peer_cert_info(const mbedtls_ssl_context *ssl)
{
    const mbedtls_x509_crt *cert;
    const size_t buf_size = 1024;
    char *buf = calloc(buf_size, sizeof(char));
    if (buf == NULL) {
        ESP_LOGE(TAG, "Out of memory - Callback execution failed!");
        return;
    }

    // Logging the peer certificate info
    cert = mbedtls_ssl_get_peer_cert(ssl);
    if (cert != NULL) {
        mbedtls_x509_crt_info((char *) buf, buf_size - 1, "    ", cert);
        ESP_LOGI(TAG, "Peer certificate info:\n%s", buf);
    } else {
        ESP_LOGW(TAG, "Could not obtain the peer certificate!");
    }

    free(buf);
}