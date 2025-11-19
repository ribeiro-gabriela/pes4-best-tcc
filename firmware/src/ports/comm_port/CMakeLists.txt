idf_component_register(SRCS "comm_port.c"
                    INCLUDE_DIRS "include"
                    REQUIRES wifi_adapter esp_wifi tftp freertos)