set(srcs "tftp/tftp_client.c"
         "tftp/tftp_server.c"
         "tftp/tftp_xfer.c"
         "port/tftp_port.c")

set(include_dir "tftp"
                "port/include")

set(priv_requires console)

idf_component_register(SRCS ${srcs}
                       INCLUDE_DIRS ${include_dir}
                       PRIV_REQUIRES ${priv_requires})

target_compile_options(${COMPONENT_LIB} PRIVATE -Wno-implicit-function-declaration)
target_compile_options(${COMPONENT_LIB} PRIVATE -Wno-maybe-uninitialized)