idf_component_register(SRCS "storage_core.c"
                    REQUIRES spiffs nvs_flash
                    INCLUDE_DIRS "include")
