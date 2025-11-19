idf_component_register(SRCS "storage_adapter.c"
                    REQUIRES spiffs nvs_flash
                    INCLUDE_DIRS "include")
