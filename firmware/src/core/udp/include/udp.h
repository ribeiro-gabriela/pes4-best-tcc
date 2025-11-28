#ifndef UDP_ADAPTER_H
#define UDP_ADAPTER_H

#include <stdint.h>
#include <stddef.h>
#include "lwip/sockets.h"
#include "freertos/FreeRTOS.h"
#include "freertos/stream_buffer.h"

// Configurações do TFTP
#define UDP_SERVER_PORT 69
#define UDP_MAX_PAYLOAD_LEN 516

/**
 * @brief Estrutura Unificada de Pacote UDP.
 * Contém os dados E o contexto de quem enviou (necessário para responder).
 * Esta é a estrutura que trafegará pelo Stream Buffer.
 */
typedef struct {
    uint8_t payload[UDP_MAX_PAYLOAD_LEN]; // Buffer de dados estático
    size_t len;                           // Tamanho real dos dados recebidos
    struct sockaddr_storage sourceAddr;   // IP e Porta do Cliente
    socklen_t addrLen;                    // Tamanho da estrutura de endereço
} UdpPacket_t;

/**
 * @brief Inicializa o socket, o stream buffer e a task de listen.
 * @return 0 em sucesso, -1 em erro.
 */
int8_t udpAdapterInit(void);

/**
 * @brief Função para o DECODER ler um pacote do buffer.
 * @param packet Ponteiro para a estrutura onde os dados serão copiados.
 * @param ticks_to_wait Tempo máximo de espera (ex: portMAX_DELAY).
 * @return Tamanho bytes lidos do stream buffer (0 se timeout/vazio).
 */
size_t udpAdapterReceivePacket(UdpPacket_t *packet, TickType_t ticks_to_wait);

/**
 * @brief Envia uma resposta UDP para um cliente específico.
 * @param destAddr Endereço de destino (copiado do pacote recebido).
 * @param addrLen Tamanho do endereço.
 * @param data Ponteiro para os dados.
 * @param len Tamanho dos dados.
 * @return 0 em sucesso, -1 em erro.
 */
int8_t udpAdapterSend(const struct sockaddr_storage *destAddr, socklen_t addrLen, const uint8_t *data, size_t len);

#endif // UDP_ADAPTER_H
