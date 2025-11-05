idf_component_register(SRCS "tftp_server.c" "tftp_xfer.c" "tftp_port.c"
                       REQUIRES console
                       INCLUDE_DIRS "include")
