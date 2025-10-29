/*
 * Copyright (c) 2006-2022, RT-Thread Development Team
 * Copyright (c) 2024, Mr. 9You
 *
 * SPDX-License-Identifier: Apache-2.0
 */

#ifndef __TFTP_PORT_H__
#define __TFTP_PORT_H__

#include <unistd.h>
#include <fcntl.h>
#include <stdio.h>
#include <stdlib.h>
#include <stdarg.h>
#include <string.h>
#include "tftp.h"

void *tftp_file_open(const char *fname, const char *mode, int is_write);
int tftp_file_write(void *handle, int pos, void *buff, int len);
int tftp_file_read(void *handle, int pos, void *buff, int len);
void tftp_file_close(void *handle);
void *rt_memcpy(void *dest, const void *src, size_t n);
void *rt_memset(void *s, int c, size_t n);
int rt_sprintf(char *str, const char *format, ...);
char *rt_strdup(const char *s);

#endif