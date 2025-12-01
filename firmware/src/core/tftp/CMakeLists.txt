idf_component_register(SRCS "tftp_server.c" "tftp_core.c" "tftp_client.c" "../main_core/main_core.c"
			    REQUIRES hw_config udp arinc spiffs main_core
                       INCLUDE_DIRS "include")
