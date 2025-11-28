#include "tftp_client.h"
#include "freertos/FreeRTOS.h"
#include "freertos/idf_additions.h"
#include "portmacro.h"
#include "udp.h"
#include "tftp_core.h"
#include "arinc_core.h"

#include <stddef.h>
#include <stdint.h>
#include <stdio.h>
#include "esp_spiffs.h"
#include "esp_log.h"

#define TFTP_TIMEOUT_MS 2000
#define MAX_RETRIES 3
#define TFTP_DATA_SIZE 512
uint8_t recv_buf[516];

size_t ratalina = 0;

#define MESSAGE_BUFFER_SIZE (4096)

StaticMessageBuffer_t messageBufferStruct;
uint8_t messageBuffer[MESSAGE_BUFFER_SIZE];
MessageBufferHandle_t messageBufferHandle;

const char* TAG = "tftp client";

int tftpClientGet(const char* ip_addr, const char* filename)
{
    int sock = socket(AF_INET, SOCK_DGRAM, IPPROTO_IP);
    if (sock < 0) return -1;

    struct sockaddr_in server_addr = {0};
    server_addr.sin_family = AF_INET;
    server_addr.sin_port = htons(6969);
    inet_pton(AF_INET, ip_addr, &server_addr.sin_addr);

    struct timeval tv = { .tv_sec = 2, .tv_usec = 0 };
    setsockopt(sock, SOL_SOCKET, SO_RCVTIMEO, &tv, sizeof(tv));

    // creating rrq    
    char packet[516];
    size_t req_len = sprintf(packet + 2, "%s", filename) + 3 + 6; // +2 opcode, +1 null, +5 "octet", +1 null
    *(uint16_t*)packet = htons(TFTP_OP_RRQ);
    strcpy(packet + 2 + strlen(filename) + 1, "octet");

    sendto(sock, packet, req_len, 0, (struct sockaddr*)&server_addr, sizeof(server_addr));

    ESP_LOGI(TAG, "rrq sent to %s: %s", ip_addr, filename);


    

    // receiving loop
    uint16_t expected_block = 1;
    int retry = 0;
    size_t total_received = 0;


    char fPath[32];
    snprintf(fPath, 32, "/spiffs/%s", filename);
    FILE* f = fopen(fPath, "wb");

    while (1) {
        struct sockaddr_in sender;
        socklen_t slen = sizeof(sender);
        int len = recvfrom(
            sock, packet, sizeof(packet), 0, (struct sockaddr*)&sender, &slen);
        /* size_t offset = 0; */

        if (len > 4) {
            uint16_t opcode = ntohs(*(uint16_t*)packet);
            uint16_t block  = ntohs(*(uint16_t*)(packet + 2));

            if (opcode == TFTP_OP_DATA && block == expected_block) {
                uint8_t* data_ptr = (uint8_t*)packet + 4;
                size_t data_len = len - 4;

		fwrite(data_ptr, sizeof(uint8_t),data_len, f);
                
                
                // ack
                uint16_t ack_pkt[2] = { htons(TFTP_OP_ACK), htons(block) };

                sendto(sock, ack_pkt, 4, 0, (struct sockaddr*)&sender, slen);

                /* sendLur(); */

                arincStatusFileScheme_t filesList[1];
                filesList[0].headerFileNameLength = strlen(filename);
                strncpy(
                    filesList[0].headerFileName, filename, MAX_DESCRIPTION_LEN - 1);
                filesList[0].headerFileName[MAX_DESCRIPTION_LEN] = '\0';



                /* size_t bytesSent = xMessageBufferSend(messageBufferHandle, */
                /*                                       (void*)filesList, */
                /*                                       sizeof(arincStatusFileScheme_t), */
                /*                                       portMAX_DELAY); */

		/* if (bytesSent == sizeof(arincStatusFileScheme_t)) */
		/* { */
		/*     ESP_LOGI(TAG, "sending LUS file to server"); */
		/* } */
		/* else */
		/* { */
		/*     ESP_LOGE(TAG, "could not send LUS. buffer full"); */
		/* } */

                expected_block++;
                total_received += data_len;
                retry = 0;

                if (data_len < 512) {
                    ESP_LOGI(TAG,
                             "download finished. received: %d bytes",
                             total_received);

		    
		    ratalina = total_received;
                    
                    break;
		    
                }
            }
        } 
        else {
            // Timeout
            retry++;
            if (retry > MAX_RETRIES) {
                ESP_LOGE(TAG, "tftp max retries excedeed");
                goto abort;
            }
            if (expected_block == 1) {
                 sendto(sock, packet, req_len, 0, (struct sockaddr*)&server_addr, sizeof(server_addr));
            } else {
                 uint16_t ack_pkt[2] = { htons(TFTP_OP_ACK), htons(expected_block - 1) };
                 sendto(sock, ack_pkt, 4, 0, (struct sockaddr*)&server_addr, sizeof(server_addr)); // Cuidado com o endereço aqui (deve ser o da sessão)
            }
        }
    }

    fclose(f);

    close(sock);
    return 0;

abort:
    close(sock);
    return -1;
}


int tftpClientPut(const char* ip_addr, const char* filename, uint8_t* payload, size_t payload_size)
{
// 1. Setup do Socket
    int sock = socket(AF_INET, SOCK_DGRAM, IPPROTO_IP);
    if (sock < 0) return -1;

    struct sockaddr_in server_addr = {0};
    server_addr.sin_family = AF_INET;
    server_addr.sin_port = htons(69);
    inet_pton(AF_INET, ip_addr, &server_addr.sin_addr);

    struct timeval tv = { .tv_sec = 2, .tv_usec = 0 };
    setsockopt(sock, SOL_SOCKET, SO_RCVTIMEO, &tv, sizeof(tv));

    // 2. Criação do WRQ (Write Request)
    char packet[516];
    
    size_t filename_len = strlen(filename);
    size_t mode_len = strlen("octet");
    // Tamanho = 2 bytes OP + filename_len + 1 byte NULL + mode_len + 1 byte NULL
    size_t req_len = 2 + filename_len + 1 + mode_len + 1;

    *(uint16_t*)packet = htons(TFTP_OP_WRQ); // Opcode WRQ
    strcpy(packet + 2, filename);
    strcpy(packet + 2 + filename_len + 1, "octet");

    // Envia o WRQ inicial
    sendto(sock, packet, req_len, 0, (struct sockaddr*)&server_addr, sizeof(server_addr));

    ESP_LOGI(TAG, "WRQ sent to %s: %s", ip_addr, filename);
    
    // Variáveis para o loop de transferência
    uint16_t current_block = 0; // Espera ACK para Block 0
    int retry = 0;
    size_t total_sent = 0;
    // O offset inicial (posição atual de leitura no buffer)
    size_t payload_offset = 0; 

    struct sockaddr_in session_addr = {0};
    socklen_t slen = sizeof(session_addr);

    // 

    // Loop de Transferência: Recebe ACK (N) -> Envia DATA (N+1)
    while (1) {
        
        int len = recvfrom(
            sock, packet, sizeof(packet), 0, (struct sockaddr*)&session_addr, &slen);
        
        // Se este é o primeiro pacote (ACK 0), armazena o endereço da sessão
        if (current_block == 0 && len > 0) {
            server_addr = session_addr;
            ESP_LOGI(TAG, "Session established on port %d", ntohs(server_addr.sin_port));
        }

        if (len > 3) {
            uint16_t opcode = ntohs(*(uint16_t*)packet);
            uint16_t block = ntohs(*(uint16_t*)(packet + 2));

            if (opcode == TFTP_OP_ACK && block == current_block) {
                // ACK recebido corretamente. Prepara para enviar o próximo bloco.
                current_block++;
                retry = 0;
                
                // 3. Condição de Término
                // A transferência termina quando o ACK é recebido para o último pacote
                // Se o pacote anterior enviado tinha menos que TFTP_DATA_SIZE (512),
                // então ACK para 'current_block' (o último bloco enviado) significa fim.
                if (current_block > 1 && (total_sent % TFTP_DATA_SIZE != 0)) {
                    // Note: total_sent já deve ter o valor final aqui.
                    ESP_LOGI(TAG, "Upload finished. Sent: %zu bytes", total_sent);
                    break;
                }
                
                // Verifica se há mais dados para enviar
                if (payload_offset >= payload_size) {
                    // Este caso só deve ocorrer se o arquivo for exatamente múltiplo de 512.
                    // Se for, precisamos enviar um pacote DATA vazio (tamanho 4).
                    if (payload_size % TFTP_DATA_SIZE == 0 && payload_size > 0) {
                        size_t empty_data_len = 0;
                        char data_packet[4];
                        *(uint16_t*)data_packet = htons(TFTP_OP_DATA);
                        *(uint16_t*)(data_packet + 2) = htons(current_block);
                        sendto(sock, data_packet, 4, 0, (struct sockaddr*)&server_addr, sizeof(server_addr));
                        ESP_LOGI(TAG, "Sent final empty block %d", current_block);
                        // A transferência terminará no próximo loop após receber o ACK para este bloco.
                        continue;
                    }
                    // Se o ACK for para o pacote vazio final, já deve ter sido pego pelo 'break' acima.
                    // Se chegar aqui, pode ser um erro de lógica, mas por segurança, não envia mais nada.
                    ESP_LOGW(TAG, "Reached end of payload logic fallback.");
                    break; 
                }

                // 4. Preparar e Enviar o Pacote DATA (Opcode 3)
                
                // Calcula o tamanho dos dados a serem enviados neste bloco
                size_t remaining_bytes = payload_size - payload_offset;
                size_t data_len = (remaining_bytes > TFTP_DATA_SIZE) ? TFTP_DATA_SIZE : remaining_bytes;
                
                char data_packet[516];
                
                // Cópia do bloco do payload para o pacote
                memcpy(data_packet + 4, payload + payload_offset, data_len);

                // Cabeçalho do pacote DATA
                *(uint16_t*)data_packet = htons(TFTP_OP_DATA); // Opcode DATA
                *(uint16_t*)(data_packet + 2) = htons(current_block); // Número do Bloco
                
                size_t packet_len = 4 + data_len; 

                // Envia o pacote DATA
                sendto(sock, data_packet, packet_len, 0, (struct sockaddr*)&server_addr, sizeof(server_addr));
                
                total_sent = payload_offset + data_len; // Total enviado neste momento
                payload_offset += data_len; // Avança o offset para o próximo bloco
                ESP_LOGI(TAG, "Sent block %d (%zu bytes). Total sent: %zu", current_block, data_len, total_sent);
                
            } else if (opcode == TFTP_OP_ERROR) {
                // Tratamento de Erro do servidor
                uint16_t error_code = block;
                const char* error_msg = packet + 4;
                ESP_LOGE(TAG, "TFTP Server Error %d: %s", error_code, error_msg);
                goto abort;
            } else {
                // Pacote inesperado (Ignorar ou Logar)
                ESP_LOGW(TAG, "Received unexpected opcode %d or block %d (expected %d)", opcode, block, current_block);
            }
        }
        else {
            // 5. Timeout ou Pacote Inválido (Retry/Retransmissão)
            retry++;
            if (retry > MAX_RETRIES) {
                ESP_LOGE(TAG, "TFTP max retries exceeded");
                goto abort;
            }
            
            ESP_LOGW(TAG, "Timeout, retransmitting block %d (attempt %d)", current_block, retry);

            if (current_block == 0) {
                // Timeout no ACK 0 (Re-envia WRQ)
                sendto(sock, packet, req_len, 0, (struct sockaddr*)&server_addr, sizeof(server_addr));
            } else {
                // Timeout em um ACK (Re-envia o Bloco de Dados anterior: current_block)
                
                // 5a. Recalcular o offset para o início do bloco atual
                // O offset do bloco atual é o total_sent - (total_sent do último bloco)
                // Usamos o offset do bloco ANTERIOR (current_block - 1) para o cálculo.
                size_t retransmit_offset = (current_block - 1) * TFTP_DATA_SIZE;
                
                // 5b. Calcula o tamanho dos dados a serem retransmitidos
                size_t remaining_bytes = payload_size - retransmit_offset;
                size_t data_len = (remaining_bytes > TFTP_DATA_SIZE) ? TFTP_DATA_SIZE : remaining_bytes;

                char data_packet[516];
                
                // Cópia do bloco do payload para o pacote
                memcpy(data_packet + 4, payload + retransmit_offset, data_len);

                // Cabeçalho do pacote DATA
                *(uint16_t*)data_packet = htons(TFTP_OP_DATA); // Opcode DATA
                *(uint16_t*)(data_packet + 2) = htons(current_block); // Número do Bloco (O bloco que está sendo esperado o ACK)
                
                size_t packet_len = 4 + data_len;
                sendto(sock, data_packet, packet_len, 0, (struct sockaddr*)&server_addr, sizeof(server_addr));
                
                ESP_LOGW(TAG, "Retransmitted block %d (%zu bytes) from offset %zu", current_block, data_len, retransmit_offset);
            }
        }
    }
    
    // 6. Limpeza e Retorno
    close(sock);
    return 0;

abort:
    close(sock);
    return -1;
}


void taskArincSendLus(void* params)
{
    uint8_t receivedBuffer[MESSAGE_BUFFER_SIZE];
    size_t bytesReceived;

    uint8_t* arincBuf;
    for (;;)
    {
        bytesReceived = xMessageBufferReceive(messageBufferHandle,
                                              (void*)receivedBuffer,
                                              MESSAGE_BUFFER_SIZE,
                                              portMAX_DELAY);

	if (bytesReceived > 0)
	{
	    char* descriptionStatus = "operation in progress";
	    size_t descriptionStatusLen = strlen(descriptionStatus);

	    arincBuf = (uint8_t*) malloc(bytesReceived * sizeof(uint8_t));
	    size_t bufLen = 0;
	    genLoadUploadingStatus(ARINC_OPERATION_IN_PROGRESS,
				   (uint8_t)descriptionStatusLen, descriptionStatus, 1, 20, 1, (arincStatusFileScheme_t*) receivedBuffer, arincBuf, 2500, &bufLen);

            tftpClientPut(
                "192.168.4.2", "EMB-HW-002-021-003.LUS", arincBuf, bufLen);

	    free(arincBuf);
	}

        vTaskDelay(10 / portTICK_PERIOD_MS);
    }
}

void initTaskSendLus(void)
{
    
  messageBufferHandle = xMessageBufferCreateStatic(MESSAGE_BUFFER_SIZE, messageBuffer, &messageBufferStruct);

  if (messageBufferHandle == NULL)
  {
    ESP_LOGE(TAG, "could not create message buffer");
  }
  else
  {
    ESP_LOGI(TAG, "message buffer created");
    }
  
    xTaskCreate(taskArincSendLus, "LUS sender", 9000, NULL, 5, NULL);

}
