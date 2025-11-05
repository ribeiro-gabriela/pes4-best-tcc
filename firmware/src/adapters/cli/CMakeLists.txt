idf_component_register(SRCS "cli_commands_handler.c" "cli.c"
                    REQUIRES console spiffs hashing core_adapter
                    INCLUDE_DIRS "include" "../")
