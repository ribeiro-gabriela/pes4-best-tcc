
#ifndef TFTP_PROTOCOL_H
#define TFTP_PROTOCOL_H

#include <stdint.h>
#include "udp.h" // Para ter acesso a UdpPacket_t

// Opcodes TFTP (RFC 1350)
#define TFTP_OP_RRQ   1
#define TFTP_OP_WRQ   2
#define TFTP_OP_DATA  3
#define TFTP_OP_ACK   4
#define TFTP_OP_ERROR 5

#define TFTP_SESSION_STACK_SIZE 12000
#define TFTP_SESSION_PRIORITY   4 // Prioridade menor que o decoder/listener

typedef struct {
    uint16_t opcode;
    char filename[128]; // Tamanho seguro para nome de arquivo
    struct sockaddr_storage clientAddr;
    socklen_t addrLen;
} TftpSessionConfig_t;

void tftp_session_task(void *pvParameters);
void tftp_decoder_task(void);

#endif // TFTP_PROTOCOL_H
