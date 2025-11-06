idf_component_register(SRCS "cli_commands_handler.c" "cli.c"
                    REQUIRES console spiffs hashing main_core
                    INCLUDE_DIRS "include" "../")
