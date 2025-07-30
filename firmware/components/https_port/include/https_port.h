#ifndef _HTTPS_PORT_H
#define _HTTPS_PORT_H

#include "esp_https_server.h"
#include "esp_log.h"

void https_event_handler(void* arg, esp_event_base_t event_base, 
                        int32_t event_id, void* event_data);

httpd_handle_t start_webserver();

void init_https_server();

esp_err_t get_hello_handler(httpd_req_t* request);


#endif