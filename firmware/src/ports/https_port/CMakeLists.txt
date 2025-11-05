idf_component_register(SRCS "https_port.c"
                    INCLUDE_DIRS "include"
                    REQUIRES esp_https_server
                    EMBED_TXTFILES  "certs/server_cert.pem"
                                    "certs/server_key.pem")
