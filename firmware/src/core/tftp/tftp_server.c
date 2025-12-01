#include "freertos/idf_additions.h"
#include "portmacro.h"
#include "tftp_core.h"
#include "esp_log.h"
#include "lwip/sockets.h"
#include <stddef.h>
#include <stdint.h>
#include <string.h>

#include "arinc_core.h"
#include "tftp_client.h"
#include "main_core.h"

static const char *TAG = "tftp_session";

#define TFTP_PACKET_BUFFER_SIZE 516

extern QueueHandle_t BCQueue;

static int sendAck(int sock, struct sockaddr_storage *destAddr, socklen_t addrLen, uint16_t blockNumber)
{
    uint8_t packet[4];
    // Header ACK: [Opcode: 2 bytes] [Block #: 2 bytes]
    uint16_t opcode = htons(TFTP_OP_ACK);
    uint16_t block = htons(blockNumber);
    
    memcpy(&packet[0], &opcode, 2);
    memcpy(&packet[2], &block, 2);

    return sendto(sock, packet, 4, 0, (struct sockaddr *)destAddr, addrLen);
}

static void send_error(int sock, struct sockaddr_storage *destAddr, socklen_t addrLen, uint16_t errorCode, const char *errMsg)
{
    uint8_t packet[128];
    uint16_t opcode = htons(TFTP_OP_ERROR);
    uint16_t code = htons(errorCode);
    
    memcpy(&packet[0], &opcode, 2);
    memcpy(&packet[2], &code, 2);
    strncpy((char *)&packet[4], errMsg, 100);
    
    size_t len = 4 + strlen(errMsg) + 1;
    sendto(sock, packet, len, 0, (struct sockaddr *)destAddr, addrLen);
}

static int send_data(int sock, struct sockaddr_storage *destAddr, socklen_t addrLen,
                     uint16_t blockNumber, const uint8_t *data, size_t dataLen)
{
    size_t packetLen = 4 + dataLen;
    uint8_t packet[TFTP_PACKET_BUFFER_SIZE]; 
    
    uint16_t opcode = htons(TFTP_OP_DATA);
    uint16_t block = htons(blockNumber);
    
    memcpy(&packet[0], &opcode, 2);
    memcpy(&packet[2], &block, 2);

    memcpy(&packet[4], data, dataLen);

    int err = sendto(sock, packet, packetLen, 0, (struct sockaddr *)destAddr, addrLen);
    
    if (err < 0) {
        ESP_LOGE(TAG, "Erro durante envio DATA Bloco %d: errno %d", blockNumber, errno);
        return -1;
    }
    return 0;
}


void tftp_session_task(void *pvParameters)
{
    TftpSessionConfig_t *config = (TftpSessionConfig_t *)pvParameters;
    
    ESP_LOGI(TAG, "Sessão iniciada para arquivo: %s", config->filename);

    int session_socket = -1;
    struct sockaddr_in my_addr;
    uint8_t *packet_buffer = NULL;

    packet_buffer = (uint8_t *)malloc(TFTP_PACKET_BUFFER_SIZE);
    if (packet_buffer == NULL) {
        ESP_LOGE(TAG, "Falha de memória no buffer de sessão");
        goto cleanup;
    }

    session_socket = socket(AF_INET, SOCK_DGRAM, IPPROTO_IP);
    if (session_socket < 0) {
        ESP_LOGE(TAG, "Falha ao criar socket de sessão");
        goto cleanup;
    }

    memset(&my_addr, 0, sizeof(my_addr));
    my_addr.sin_family = AF_INET;
    my_addr.sin_port = htons(0);
    my_addr.sin_addr.s_addr = htonl(INADDR_ANY);

    if (bind(session_socket, (struct sockaddr *)&my_addr, sizeof(my_addr)) < 0) {
        ESP_LOGE(TAG, "Falha no bind da sessão");
        goto cleanup;
    }
    
    struct timeval timeout;
    timeout.tv_sec = 3;
    timeout.tv_usec = 0;
    setsockopt(session_socket, SOL_SOCKET, SO_RCVTIMEO, &timeout, sizeof(timeout));

    if (config->opcode == TFTP_OP_WRQ) 
    {
        ESP_LOGI(TAG, "ok I received a write req");
        
        sendAck(session_socket, &config->clientAddr, config->addrLen, 0);

        uint16_t expected_block = 1;
        arinc_reset_buffer();
        
        while (1) {
            struct sockaddr_storage sender_addr;
            socklen_t sender_len = sizeof(sender_addr);
            
            // Espera pacote DATA
            int len = recvfrom(session_socket, packet_buffer, TFTP_PACKET_BUFFER_SIZE, 0, 
                               (struct sockaddr *)&sender_addr, &sender_len);

            if (len > 0) {
                // Parse Opcode
                uint16_t recv_opcode;
                memcpy(&recv_opcode, packet_buffer, 2);
                recv_opcode = ntohs(recv_opcode);

                if (recv_opcode == TFTP_OP_DATA) {
                    uint16_t recv_block;
                    memcpy(&recv_block, packet_buffer + 2, 2);
                    recv_block = ntohs(recv_block);

                    if (recv_block == expected_block) {
                        // DADOS VÁLIDOS!
                        size_t data_len = len - 4;
                        uint8_t *data_ptr = packet_buffer + 4;

                        arincErr_t writeRes =
			    arinc_append_data(data_ptr, data_len);

                        if (writeRes != ARINC_ERR_OK)
                        {
                            send_error(session_socket,
                                       &config->clientAddr,
                                       config->addrLen,
                                       3,
                                       "Disk/Buffer Full");
                            break; // Aborta a transferência
                        }

                        ESP_LOGD(TAG,
                                 "Recebido Bloco %d (%d bytes)",
                                 recv_block,
                                 (int)data_len);

                        // Confirma recebimento
                        sendAck(session_socket, &config->clientAddr, config->addrLen, recv_block);
                        expected_block++;

                        // Se o pacote for menor que 512 bytes, é o último.
                        if (data_len < 512) {
                            ESP_LOGI(TAG, "wrq transfer finished");

                            const uint8_t* final_ptr;
                            size_t final_size;
                            arinc_get_raw_buffer(&final_ptr, &final_size);

                            ESP_LOGI(TAG, " -> %d bytes", (int)final_size);

                            ARINC_DATA_TYPE_t filetype = ARINC_NONE;
                            arincErr_t isFileValid =
                                arincValidateFileAndGetName(config->filename,
                                                            filetype);

                            uint8_t receivedFile[MAX_LUR_SIZE] = {0};
			    size_t fLen = 0;

                            if (isFileValid == ARINC_ERR_OK)
                            {
                                // sending queue event
                                QueueMessage_t eventMessage;
                                eventMessage.eventID = LOAD_REQUEST;
                                sprintf((char*)eventMessage.logMessage,
					"received Load Uploading Request");

				if (xQueueSend(BCQueue,
					       (void*)&eventMessage,
					       portMAX_DELAY) != pdPASS)
				    {
				      ESP_LOGE(TAG, "failed to send message to BCQueue");
				    }
			    }

                            lurFilesDescriptionHeader_t filesList[MAX_FILE_PER_TRANSFER] = {0};

                            uint16_t parsedCount = 0;

                            arincErr_t res =
                                readLoadUploadingRequest(final_size,
                                                         final_ptr,
                                                         filesList,
                                                         &parsedCount);

                            if (res == ARINC_ERR_OK)
                            {
                                ESP_LOGI(TAG,
                                         "LUR Parseado com sucesso. %d "
                                         "arquivos encontrados.",
                                         parsedCount);

				tftpClientGet("192.168.4.2", filesList[0].loadPartNumberName);

				
                            }
                            else
                            {
			      ESP_LOGE(TAG, "LUR Corrompido ou Inválido. %d", res);
                            }

                            break;
                        }
                    } else if (recv_block < expected_block) {
                        // Retransmissão (ACK perdido), reenvia ACK anterior
                        sendAck(session_socket, &config->clientAddr, config->addrLen, recv_block);
                    }
                }
            } else {
                ESP_LOGW(TAG, "timeout waiting data");
                break; 
            }
        }
    }
    else if (config->opcode == TFTP_OP_RRQ)
    {
	ARINC_DATA_TYPE_t filetype = ARINC_NONE;
        arincErr_t isFileValid =
            arincValidateFileAndGetName(config->filename, filetype);


	uint8_t generatedLuiFile[MAX_LUI_FILE] = {0};
	size_t fLen = 0;

        if (isFileValid == ARINC_ERR_OK)
        {
            ESP_LOGW(TAG, "RECEBI UM AQUIVO ARINC");
	    arincErr_t err = loadUploadingInitialization(
							 ARINC_OPERATION_ACCEPTED, NULL, generatedLuiFile, &fLen);

	    ESP_LOGW(TAG, "tamanho %lu", fLen);

        }
        else
        {
            ESP_LOGE(TAG, "o arinc não deu certo");
	    loadUploadingInitialization(ARINC_OPERATION_NOT_ACCEPTED, (uint8_t*) "invalid file name", generatedLuiFile, &fLen);
        }

	uint16_t block_number = 1;
	size_t offset = 0;
	uint8_t retryCount = 0;

        while (offset < fLen)
        {
            // 2. Ler o bloco (máx 512 bytes)
            size_t bytesToRead = fLen - offset;
            if (bytesToRead > 512)
            {
                bytesToRead = 512;
            }


            // 3. Enviar o pacote DATA
            int res = send_data(session_socket,
                                &config->clientAddr,
                                config->addrLen,
                                block_number, generatedLuiFile + offset, bytesToRead);

            // 4. Esperar o ACK (Lógica de Retransmissão aqui)
            // ... recvfrom() bloqueante esperando ACK ...

	    
            uint8_t arincDataResponse[128];
            int len = recvfrom(session_socket,
                               arincDataResponse,
                               TFTP_PACKET_BUFFER_SIZE,
                               0,
                               (struct sockaddr*)&config->clientAddr,
                               &config->addrLen);
	    bool ackReceived = false;

	    if (len > 0)
	    {
		uint16_t recv_opcode;
		memcpy(&recv_opcode, arincDataResponse, 2);
		recv_opcode = ntohs(recv_opcode);
                if (recv_opcode == TFTP_OP_ACK)
                {
                    uint16_t blockNo;
                    memcpy(&blockNo, arincDataResponse + 2, 2);
		    blockNo = ntohs(blockNo);

                    if (blockNo == block_number)
                    {
                        offset += bytesToRead;
			ackReceived = true;
			retryCount = 0;
                        block_number++;
                        continue;
                    }
                }
                else
                {
                    send_error(session_socket,
                               &config->clientAddr,
                               config->addrLen,
                               0,
                               "invalid package");
                    
                }

		if(!ackReceived)
		  {
		    retryCount++;
		    ESP_LOGW(TAG, "ack not received, trying once more");

		    if(retryCount > 1)
		      {
			ESP_LOGE(TAG, "max retries exceeded");
			break;
		      }
		  }
		
            }

            // 5. Se o ACK for recebido, avança o offset
            // ...
        }

        // arinc
        /* send_error(session_socket, &config->clientAddr, config->addrLen, 0,
         * "Read not implemented yet"); */
    }

    // so sorry for goto    
cleanup:
    if (session_socket >= 0) close(session_socket);
    if (packet_buffer != NULL) free(packet_buffer);
    
    if (config != NULL) vPortFree(config); 

    ESP_LOGI(TAG, "task ended");
    vTaskDelete(NULL);
}


