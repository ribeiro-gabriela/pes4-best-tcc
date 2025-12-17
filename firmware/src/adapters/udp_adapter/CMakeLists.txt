idf_component_register(SRCS "udp_adapter.c"
	               REQUIRES hw_config tftp_adapter
                       INCLUDE_DIRS "include")
