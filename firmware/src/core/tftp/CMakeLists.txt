idf_component_register(SRCS "tftp_server.c" "tftp_core.c" "tftp_client.c"
			    REQUIRES hw_config udp arinc spiffs
                       INCLUDE_DIRS "include")
