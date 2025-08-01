#ifndef _HTTPS_PORT_H
#define _HTTPS_PORT_H

#include "esp_https_server.h"
#include "esp_log.h"

void https_event_handler(void* arg, esp_event_base_t event_base, 
                        int32_t event_id, void* event_data);

httpd_handle_t start_webserver();

void init_https_server();

esp_err_t get_hello_handler(httpd_req_t* request);

static void https_server_user_callback(esp_https_server_user_cb_arg_t *user_cb);

static void print_peer_cert_info(const mbedtls_ssl_context *ssl);

#endif