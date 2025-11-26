idf_component_register(SRCS "comm_port.c" "../../adapters/wifi_adapter/wifi_adapter.c"
                    INCLUDE_DIRS "include"
                    REQUIRES wifi_adapter esp_wifi tftp freertos)