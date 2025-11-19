idf_component_register(SRCS "main.c"
                    PRIV_REQUIRES main_core verification_adapter
                    INCLUDE_DIRS "")
spiffs_create_partition_image(storage ../src/adapters/storage_adapter/partition FLASH_IN_PROJECT)                    
