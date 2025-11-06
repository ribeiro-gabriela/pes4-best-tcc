idf_component_register(SRCS "main_core.c"
                    REQUIRES fsm_core cli hashing tftp storage_core wifi_core freertos
                    INCLUDE_DIRS "include")
