#include "udp_adapter.h"

#include "esp_log.h"
#include "freertos/idf_additions.h"
#include "lwip/err.h"
#include "lwip/sockets.h"
#include "lwip/sys.h"
#include <stdint.h>
#include <string.h>

static const char* TAG = "UDP";

static int serverSocket = -1;

#define UDP_RECV_PKG_SIZE (sizeof(UdpPacket_t) * 2)
#define TRIGGER_LEVEL 1

static uint8_t udpReceivedPacketsBuf[UDP_RECV_PKG_SIZE];
static StaticStreamBuffer_t udpReceivedPacketsStruct;
static StreamBufferHandle_t udpReceivedPacketsHandle = NULL;

#define LISTENER_STACK_SIZE 4096
static StackType_t listenerStack[LISTENER_STACK_SIZE];
static StaticTask_t listenerTaskBuffer;
static TaskHandle_t listenerTaskHandle;

static void udpListenTask(void* params)
{
    UdpPacket_t tempPacket;

    for (;;)
    {
        tempPacket.addrLen = sizeof(tempPacket.sourceAddr);

        int len = recvfrom(serverSocket,
                           tempPacket.payload,
                           UDP_MAX_PAYLOAD_LEN,
                           0,
                           (struct sockaddr*)&tempPacket.sourceAddr,
                           &tempPacket.addrLen);
        tempPacket.payload[len] = '\0';

        if (len < 0)
        {
            if (errno != EAGAIN && errno != EWOULDBLOCK)
            {
                ESP_LOGE(TAG, "recvfrom failed: errno %d", errno);
            }
            continue;
        }

        if (len > 0)
        {
            tempPacket.len = (size_t)len;

            size_t bytesSent = xStreamBufferSend(
                udpReceivedPacketsHandle, (void*)&tempPacket, sizeof(UdpPacket_t), 0);

            if (bytesSent != sizeof(UdpPacket_t))
            {
                ESP_LOGW(TAG, "stream buffer full. packet lost");
            }
            else
            {
                ESP_LOGD(TAG, "%d bytes allocated on buffer", len);
            }
        }
    }
}

int8_t initUdpAdapter(void)
{
    udpReceivedPacketsHandle = xStreamBufferCreateStatic(
        UDP_RECV_PKG_SIZE, TRIGGER_LEVEL, udpReceivedPacketsBuf, &udpReceivedPacketsStruct);
    if (udpReceivedPacketsHandle == NULL)
    {
        ESP_LOGE(TAG, "could not create stream buffer");
        return -1;
    }

    serverSocket = socket(AF_INET, SOCK_DGRAM, IPPROTO_IP);
    if (serverSocket < 0)
    {
        ESP_LOGE(TAG, "could not create socket: errno %d", errno);
        return -1;
    }

    struct sockaddr_in serverAddr;
    serverAddr.sin_addr.s_addr = htonl(INADDR_ANY);
    serverAddr.sin_family = AF_INET;
    serverAddr.sin_port = htons(UDP_SERVER_PORT);

    if (bind(serverSocket, (struct sockaddr*)&serverAddr, sizeof(serverAddr)) < 0)
    {
        ESP_LOGE(TAG, "Falha no bind: errno %d", errno);
        close(serverSocket);
        return -1;
    }

    struct timeval timeout;
    timeout.tv_sec = 1;
    timeout.tv_usec = 0;
    setsockopt(serverSocket, SOL_SOCKET, SO_RCVTIMEO, &timeout, sizeof(timeout));

    ESP_LOGI(TAG, "socket bound on port %d", UDP_SERVER_PORT);

    listenerTaskHandle = xTaskCreateStaticPinnedToCore(udpListenTask,
                                                       "udp_listen",
                                                       LISTENER_STACK_SIZE,
                                                       NULL,
                                                       5,
                                                       listenerStack,
                                                       &listenerTaskBuffer,
                                                       1);
    if (listenerTaskHandle == NULL)
    {
        ESP_LOGE(TAG, "could not create udp listener task");
    }

    return 0;
}

void deinitUdpAdapter(void)
{
    vSemaphoreDelete(udpReceivedPacketsHandle);
    vTaskDelete(listenerTaskHandle);

    if (serverSocket != -1)
    {
	close(serverSocket);
    }
    ESP_LOGI(TAG, "deinitializing udp adapter");
}

size_t udpAdapterReceivePacket(UdpPacket_t* packet, TickType_t wait)
{
    if (udpReceivedPacketsHandle == NULL || packet == NULL)
        return 0;

    return xStreamBufferReceive(udpReceivedPacketsHandle, (void*)packet, sizeof(UdpPacket_t), wait);
}

int8_t udpAdapterSend(const struct sockaddr_storage* destAddr,
                      socklen_t addrLen,
                      const uint8_t* data,
                      size_t len)
{
    if (serverSocket < 0)
        return -1;

    int err = sendto(serverSocket, data, len, 0, (struct sockaddr*)destAddr, addrLen);

    if (err < 0)
    {
        ESP_LOGE(TAG, "err sendto: errno %d", errno);
        return -1;
    }
    return 0;
}
