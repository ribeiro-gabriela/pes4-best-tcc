idf_component_register(SRCS "cli_port.c" "../../adapters/cli_adapter/cli.c"
                    REQUIRES cli_adapter
                    INCLUDE_DIRS "include")