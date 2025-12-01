#ifndef TFTP_CLIENT__H
#define TFTP_CLIENT__H

#include <stdint.h>
#include <stddef.h>



int tftpClientGet(const char* ip_addr, const char* filename);
int tftpClientPut(const char* ip_addr, const char* filename, uint8_t* payload, size_t payload_size);
void initTaskSendLus(void);
void deinitTaskSendLus();

size_t getImageFileSize(void);
void getImageFileName(char* out);

#endif
