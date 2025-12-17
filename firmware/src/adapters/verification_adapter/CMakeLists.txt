idf_component_register(SRCS "hashing.c" "hwid.c"
                    REQUIRES mbedtls spiffs storage_adapter tftp_adapter
                    INCLUDE_DIRS "include")
                    
