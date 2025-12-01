idf_component_register(SRCS "main_core.c"
                    REQUIRES fsm cli_port verification_port tftp storage_port comm_port freertos
                    INCLUDE_DIRS "include")
