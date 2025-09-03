/*
 * Copyright (c) 2006-2022, RT-Thread Development Team
 * Copyright (c) 2024, Mr. 9You
 *
 * SPDX-License-Identifier: Apache-2.0
 */

#include <unistd.h>
#include <fcntl.h>
#include <stdio.h>
#include <stdlib.h>
#include <stdarg.h>
#include <string.h>
#include "tftp.h"

#include "argtable3/argtable3.h"

#include "esp_console.h"
#include "esp_err.h"

#include "freertos/FreeRTOS.h"
#include "freertos/task.h"

void *tftp_file_open(const char *fname, const char *mode, int is_write)
{
    int fd = 0;
    char *fname_local = (char *)fname;
    if (fname[0] == '/' && fname[1] == '/') {
        fname_local = (char *)(fname + 1);
    }

    if (!strcmp(mode, "octet")) {
        if (is_write) {
            fd = open(fname_local, O_WRONLY | O_CREAT, 0);
        } else {
            fd = open(fname_local, O_RDONLY, 0);
        }
    } else {
        printf("tftp: No support this mode(%s).", mode);
    }

    return (void *)fd;
}

int tftp_file_write(void *handle, int pos, void *buff, int len)
{
    int fd = (int)handle;

    return write(fd, buff, len);
}

int tftp_file_read(void *handle, int pos, void *buff, int len)
{
    int fd = (int)handle;

    return read(fd, buff, len);
}

void tftp_file_close(void *handle)
{
    close((int)handle);
}

void *rt_memcpy(void *dest, const void *src, size_t n)
{
    return memcpy(dest, src, n);
}

void *rt_memset(void *s, int c, size_t n)
{
    return memset(s, c, n);
}

int rt_sprintf(char *str, const char *format, ...)
{
    va_list args;
    va_start(args, format);
    int result = vsprintf(str, format, args);
    va_end(args);
    return result;
}

char *rt_strdup(const char *s)
{
    char *d = strdup(s);
    if (d == NULL) {
        // Handle memory allocation failure
        return NULL;
    }
    return d;
}

static struct {
    struct arg_lit *server;
    struct arg_int *port;
    struct arg_str *path;
    struct arg_end *end;
} tftp_args;

static struct tftp_server *server;

static void tftp_server_thread(void *param)
{
    tftp_server_run((struct tftp_server *)param);
    server = NULL;

    vTaskDelete(NULL);
}

static int tftp_main(int argc, char **argv)
{
    int port = 0;
    const char *path = NULL;

    int nerrors = arg_parse(argc, argv, (void **) &tftp_args);

    if (nerrors != 0) {
        arg_print_errors(stderr, tftp_args.end, argv[0]);
        return 1;
    }

    if (tftp_args.server->count != 0) {
        if (tftp_args.port->count == 0) {
            port = 69;
        } else {
            port = tftp_args.port->ival[0];
        }
        if (tftp_args.path->count == 0) {
            path = "/";
        } else {
            path = tftp_args.path->sval[0];
        }
    } else {
        printf("only support tftp server mode.\n");
        return 1;
    }

    if (server) {
        printf("tftp server is already running.\n");
        return 0;
    }

    server = tftp_server_create(path, port);
    tftp_server_write_set(server, 1);
    if (xTaskCreate(tftp_server_thread, "tftps", 4096, server, 5, NULL) != pdTRUE) {
        return 1;
    }

    return 0;
}

void register_tftp(void)
{
    tftp_args.server = arg_lit0("s", "server", "run in server mode");
    tftp_args.port = arg_int0("p", "port", "<port>", "server port to listen on/connect to");
    tftp_args.path = arg_str0(NULL, NULL, "<path>", "path of the file or folder");
    tftp_args.end = arg_end(3);

    const esp_console_cmd_t cmd = {
        .command = "tftp",
        .help = "Start tftp server or client",
        .hint = NULL,
        .func = &tftp_main,
        .argtable = &tftp_args
    };
    ESP_ERROR_CHECK( esp_console_cmd_register(&cmd) );
}
