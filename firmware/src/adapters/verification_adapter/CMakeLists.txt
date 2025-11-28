idf_component_register(SRCS "hashing.c" "hwid.c"
                    REQUIRES mbedtls spiffs storage_adapter tftp
                    INCLUDE_DIRS "include")
                    
