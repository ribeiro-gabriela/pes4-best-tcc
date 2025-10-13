idf_component_register(SRCS "main.c"
                    PRIV_REQUIRES spi_flash wifi_core https_port hashing storage_core cli tftp
                    INCLUDE_DIRS "")
spiffs_create_partition_image(storage ../components/storage_core/partition FLASH_IN_PROJECT)                    
