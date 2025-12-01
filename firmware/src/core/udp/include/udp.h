#ifndef UDP_ADAPTER_H
#define UDP_ADAPTER_H

#include <stdint.h>
#include <stddef.h>
#include "lwip/sockets.h"
#include "freertos/FreeRTOS.h"
#include "freertos/stream_buffer.h"

#define UDP_SERVER_PORT 69
#define UDP_MAX_PAYLOAD_LEN 516

typedef struct {
    uint8_t payload[UDP_MAX_PAYLOAD_LEN]; 
    size_t len;                           
    struct sockaddr_storage sourceAddr;   
    socklen_t addrLen;                    
} UdpPacket_t;

int8_t initUdpAdapter(void);
void deinitUdpAdapter(void);
  
size_t udpAdapterReceivePacket(UdpPacket_t *packet, TickType_t ticks_to_wait);

int8_t udpAdapterSend(const struct sockaddr_storage *destAddr, socklen_t addrLen, const uint8_t *data, size_t len);

#endif // UDP_ADAPTER_H
