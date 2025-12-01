#include "udp.h"

#include "esp_log.h"
#include "lwip/err.h"
#include "lwip/sys.h"
#include <stdint.h>
#include <string.h>

static const char *TAG = "udp_adapter";

static int serverSocket = -1;

#define UDP_RECV_PKG_SIZE (sizeof(UdpPacket_t) * 2)
#define TRIGGER_LEVEL 1 

static uint8_t udpReceivedPacketsBuf[UDP_RECV_PKG_SIZE];
static StaticStreamBuffer_t udpReceivedPacketsStruct;
static StreamBufferHandle_t udpReceivedPacketsHandle = NULL;


#define LISTENER_STACK_SIZE 4096
static StackType_t listenerStack[LISTENER_STACK_SIZE];
static StaticTask_t listenerTaskBuffer;


static void udpListenTask(void *params)
{
    UdpPacket_t tempPacket;

    for (;;) {
        tempPacket.addrLen = sizeof(tempPacket.sourceAddr);

        int len = recvfrom(serverSocket,
                           tempPacket.payload,
                           UDP_MAX_PAYLOAD_LEN,
                           0,
                           (struct sockaddr*)&tempPacket.sourceAddr,
                           &tempPacket.addrLen);
	tempPacket.payload[len] = '\0';

     
        if (len < 0) {
            if (errno != EAGAIN && errno != EWOULDBLOCK) {
                ESP_LOGE(TAG, "recvfrom failed: errno %d", errno);
            }
            continue; 
        }
        
        if (len > 0) {
            tempPacket.len = (size_t)len;

            size_t bytesSent = xStreamBufferSend(udpReceivedPacketsHandle,
                                                 (void *)&tempPacket,
                                                 sizeof(UdpPacket_t),
                                                 0);

            if (bytesSent != sizeof(UdpPacket_t))
            {
                ESP_LOGW(TAG, "stream buffer full. packet lost");
            } else {
                ESP_LOGD(TAG, "%d bytes allocated on buffer", len);
            }
        }
    }
}

int8_t udpAdapterInit(void)
{
    udpReceivedPacketsHandle = xStreamBufferCreateStatic(UDP_RECV_PKG_SIZE,
                                              TRIGGER_LEVEL,
                                              udpReceivedPacketsBuf,
                                              &udpReceivedPacketsStruct);
    if (udpReceivedPacketsHandle == NULL) {
        ESP_LOGE(TAG, "could not create stream buffer");
        return -1;
    }

    serverSocket = socket(AF_INET, SOCK_DGRAM, IPPROTO_IP);
    if (serverSocket < 0) {
        ESP_LOGE(TAG, "could not create socket: errno %d", errno);
        return -1;
    }

    struct sockaddr_in serverAddr;
    serverAddr.sin_addr.s_addr = htonl(INADDR_ANY);
    serverAddr.sin_family = AF_INET;
    serverAddr.sin_port = htons(UDP_SERVER_PORT);

    if (bind(serverSocket, (struct sockaddr *)&serverAddr, sizeof(serverAddr)) < 0) {
        ESP_LOGE(TAG, "Falha no bind: errno %d", errno);
        close(serverSocket);
        return -1;
    }

    struct timeval timeout;
    timeout.tv_sec = 1;
    timeout.tv_usec = 0;
    setsockopt(serverSocket, SOL_SOCKET, SO_RCVTIMEO, &timeout, sizeof(timeout));

    ESP_LOGI(TAG, "socket bound on port %d", UDP_SERVER_PORT);

    xTaskCreateStaticPinnedToCore(udpListenTask,
                                  "udp_listen",
                                  LISTENER_STACK_SIZE,
                                  NULL,
                                  5, 
                                  listenerStack,
                                  &listenerTaskBuffer,
                                  1); 

    return 0;
}

size_t udpAdapterReceivePacket(UdpPacket_t *packet, TickType_t wait)
{
    if (udpReceivedPacketsHandle == NULL || packet == NULL) return 0;

    return xStreamBufferReceive(udpReceivedPacketsHandle, (void *)packet, sizeof(UdpPacket_t), wait);
}

int8_t udpAdapterSend(const struct sockaddr_storage *destAddr, socklen_t addrLen, const uint8_t *data, size_t len)
{
    if (serverSocket < 0) return -1;

    int err = sendto(serverSocket, data, len, 0, (struct sockaddr *)destAddr, addrLen);
    
    if (err < 0) {
        ESP_LOGE(TAG, "err sendto: errno %d", errno);
        return -1;
    }
    return 0;
}























/* #include "udp.h" */
/* #include "freertos/FreeRTOS.h" */
/* #include "freertos/projdefs.h" */
/* #include "hw_config.h" */
/* #include "tftp_core.h" */

/* #include <stdint.h> */
/* #include <string.h> */

/* #include "freertos/idf_additions.h" */
/* #include "lwip/err.h" */
/* #include "lwip/sockets.h" */
/* #include "lwip/sys.h" */
/* #include <lwip/netdb.h> */
/* #include <unistd.h> */

/* #include "esp_log.h" */

/* #define PORT 69 */
/* #define UDP_TASK_STACK_SIZE 4096 */
/* #define MAX_UDP_PKT_LEN 516 */

/* static const char* TAG = "udp"; */

/* extern uint8_t dataBuffer[MAX_UDP_PKT_LEN] = {0}; */
/* extern SemaphoreHandle_t dataBufferSemaphoreHandler = NULL; */
/* static StaticSemaphore_t dataBufferMutex; */

/* // for task Listener */
/* static StackType_t UDPListenerStack[UDP_TASK_STACK_SIZE]; */
/* static StaticTask_t taskUDPListener; */


/* #define HOST_IP_ADDR "192.168.4.2" */

/* // --- SOCKETS --- */
/* static int serverListenSocket = -1; */

/* // contem o endereço do cliente */
/* typedef struct tftpSessionContext */
/* { */
/*     int socketNo;  */
/*     struct sockaddr_storage destAddr;  */
/*     socklen_t addrLen; */
/*     uint8_t sessionActive; */
/* } tftpSessionContext_t; */

/* // A sessão ativa (global para simplificar, mas idealmente seria por Task/Session) */
/* static tftpSessionContext_t activeSession = { .socketNo = -1, .sessionActive = 0 }; */


/* // --- FUNÇÕES REORGANIZADAS --- */

/* /\** */
/*  * @brief Inicializa o Socket de Escuta do Servidor (bind) na porta 69. */
/*  *\/ */
/* int8_t createUDPListenerSocket(void) */
/* { */
/*     serverListenSocket = socket(AF_INET, SOCK_DGRAM, IPPROTO_IP); */
/*     if (serverListenSocket < 0) */
/*     { */
/*         ESP_LOGE(TAG, "failed to create LISTEN socket: errno %d", errno); */
/*         return -1; */
/*     } */

/*     struct sockaddr_in serverAddr; */
/*     serverAddr.sin_addr.s_addr = htonl(INADDR_ANY);  */
/*     serverAddr.sin_family = AF_INET; */
/*     serverAddr.sin_port = htons(PORT); */

/*     int err = bind(serverListenSocket, (struct sockaddr*)&serverAddr, sizeof(serverAddr)); */
/*     if (err < 0) */
/*     { */
/*         ESP_LOGE(TAG, "could not bind for listening: errno %d", errno); */
/*         close(serverListenSocket); */
/*         serverListenSocket = -1; */
/*         return -1; */
/*     } */
/*     ESP_LOGI(TAG, "bound done. listening on port %d", PORT); */
    
/*     struct timeval timeout; */
/*     timeout.tv_sec = 5; */
/*     timeout.tv_usec = 0; */
/*     setsockopt(serverListenSocket, SOL_SOCKET, SO_RCVTIMEO, &timeout, sizeof(timeout)); */

/*     return 0; */
/* } */

/* /\** */
/*  * @brief Envia um pacote UDP para o cliente da sessão ativa. */
/*  *\/ */
/* int8_t sendUDPPacketToClient(const uint8_t* payload, size_t payload_len) */
/* { */
/*     if (activeSession.sessionActive == 0 || activeSession.socketNo < 0) */
/*     { */
/*         ESP_LOGE(TAG, "udp session not opened or not valid"); */
/*         return -1; */
/*     } */

/*     // socket usado é o ListenSocket. porque? não faço ideia */
/*     int err = sendto(activeSession.socketNo, */
/*                      payload, */
/*                      payload_len, */
/*                      0, */
/*                      (struct sockaddr*)&activeSession.destAddr, */
/*                      activeSession.addrLen); */
                     
/*     if (err < 0) */
/*     { */
/*         ESP_LOGE(TAG, "error during send: errno %d", errno); */
/*         return -1; */
/*     } */

/*     return 0; */
/* } */

/* /\** */
/*  * @brief Task de Escuta UDP (Servidor) */
/*  *\/ */
/* void tUDPListen(void* params) */
/* { */
/*     if (serverListenSocket < 0) { */
/*         ESP_LOGE(TAG, "listen socket not initialized, leaving now ..."); */
/*         vTaskDelete(NULL); */
/*     } */
    
/*     struct sockaddr_storage source_addr;  */
/*     socklen_t socklen = sizeof(source_addr); */

/*     activeSession.socketNo = serverListenSocket; */

/*     ESP_LOGI(TAG, "listen task created"); */
    
/*     TaskHandle_t decoderTask; */
/*     for (;;) */
/*     { */
       
/*       if (xSemaphoreTake(dataBufferSemaphoreHandler, portMAX_DELAY) == pdTRUE) */
/* 	{ */
/* 	  ESP_LOGW(TAG, "listener took the semaphore"); */

/* 	    memset(dataBuffer, 0, sizeof(dataBuffer)); */

/* 	    int len = recvfrom(serverListenSocket,  */
/* 			    dataBuffer,  */
/* 			    MAX_BUFFER_LEN - 1,  */
/* 			    0,  */
/* 			    (struct sockaddr*)&source_addr,  */
/* 			    &socklen); */

/* 	    if (len > 0) */
/* 	    { */
/* 		activeSession.sessionActive = 1; */
/* 		activeSession.addrLen = socklen; */
/* 		memcpy(&activeSession.destAddr, &source_addr, socklen); */

/* 		ESP_LOGI(TAG, "received %d bytes. %s.", len, dataBuffer); */


/* 		decoderTask = getDecoderTaskHandler(); */
/* 		if (decoderTask != NULL) */
/* 		{ */
/* 		    ESP_LOGI(TAG, "giving notification to decoder"); */
/* 		    xTaskNotify(decoderTask, len, eSetValueWithOverwrite); */
/* 		} */

/* 	    }  */
/* 	    xSemaphoreGive(dataBufferSemaphoreHandler); */
/* 	    ESP_LOGW(TAG, "listener gave the semaphore"); */

/*         } */
/*       vTaskDelay(10 / portTICK_PERIOD_MS); */
/*     } */
/* } */

/* /\** */
/*  * @brief Cria a Task de Escuta, incluindo a inicialização do socket. */
/*  *\/ */
/* int8_t createUDPListenerTask(void) */
/* { */
/*     if (createUDPListenerSocket() != 0) */
/*     { */
/*         ESP_LOGE(TAG, "failed to initialize listener socket"); */
/*         return -1; */
/*     } */

/*     dataBufferSemaphoreHandler = xSemaphoreCreateMutexStatic(&dataBufferMutex); */
    
/*     xTaskCreateStaticPinnedToCore(tUDPListen, */
/*                                   "udp listen", */
/*                                   UDP_TASK_STACK_SIZE, */
/*                                   NULL, */
/*                                   9, */
/*                                   UDPListenerStack, */
/*                                   &taskUDPListener, */
/*                                   1); */
                                  
/*     ESP_LOGI(TAG, "already listening for packets"); */
/*     return 0; */
/* } */
