idf_component_register(SRCS "verification_port.c"
                    REQUIRES verification_adapter main_core tftp_adapter
                    INCLUDE_DIRS "include")