idf_component_register(SRCS "tftp_adapter.c" "tftp_server.c" "tftp_client.c" "../../core/main_core/main_core.c"
			    REQUIRES hw_config udp_adapter arinc_adapter spiffs main_core
                INCLUDE_DIRS "include")
