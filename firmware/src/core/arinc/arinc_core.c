#include "arinc_core.h"
#include "cc.h"
#include "esp_log.h"
#include "freertos/idf_additions.h"
#include "hw_config.h"
#include <stddef.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>

static uint8_t arincDataBuffer[MAX_LUR_SIZE] = {0}; // here to save stack mem
static size_t arincDataBufferOffset = 0;
StaticSemaphore_t arincBufferSemaphore;
SemaphoreHandle_t arincBufferSemaphoreHandle;

static const char* TAG = "arinc";

const uint8_t protocolVersion[2] = {0x41, 0x34}; // version A4

const size_t FIXED_LUS_HEADER_SIZE = sizeof(uint32_t) + (6 * sizeof(uint16_t)) +
                                     sizeof(uint8_t) + (3 * sizeof(char));
const size_t FIXED_LUS_FILE_ITEM_SIZE =
    (6 * sizeof(uint8_t)) + sizeof(uint16_t);

arincErr_t initArinc(void)
{
    arincBufferSemaphoreHandle =
        xSemaphoreCreateMutexStatic(&arincBufferSemaphore);

    if (arincBufferSemaphoreHandle == NULL)
    {
        ESP_LOGE(TAG, "could not create mutex for arinc buffer");
        return ARINC_ERR_NO_MEM;
    }

    ESP_LOGI(TAG, "mutex for arinc buffer created successfully");

    return ARINC_ERR_OK;
}

void deinitArinc(void)
{
  vSemaphoreDelete(arincBufferSemaphoreHandle);
}    


arincErr_t loadUploadingInitialization(ARINC_STATUS_CODE_t opStatusCode,
                                       uint8_t* description,
                                       uint8_t buf[MAX_LUI_FILE],
                                       size_t* bufSize)
{
    size_t offset = 0;

    // File Length
    if (offset + 4 > MAX_LUI_FILE)
        return ARINC_ERR_NO_MEM;
    offset += 4;

    // Protocol Version
    if (offset + 2 > MAX_LUI_FILE)
        return ARINC_ERR_NO_MEM;
    memcpy(buf + offset, protocolVersion, 2);
    offset += 2;

    // op acceptance status code
    if (offset + 2 > MAX_LUI_FILE)
        return ARINC_ERR_NO_MEM;
    uint16_t netOpCode = htons(opStatusCode);
    memcpy(buf + offset, &netOpCode, 2);
    offset += 2;

    // description length
    if (offset + 1 > MAX_LUI_FILE)
        return ARINC_ERR_NO_MEM;
    uint8_t descLen = (description != NULL) ? strlen((char*)description) : 0;
    buf[offset++] = descLen;

    if (descLen > 0)
    {
        if (offset + descLen > MAX_LUI_FILE)
            return ARINC_ERR_NO_MEM;
        memcpy(buf + offset, description, descLen);
        offset += descLen;
    }

    uint32_t totalSize = (uint32_t)offset;
    uint32_t netTotalSize = htonl(totalSize);

    memcpy(buf, &netTotalSize, 4);

    *bufSize = totalSize;

    return ARINC_ERR_OK;
}

arincErr_t readLoadUploadingRequest(size_t fileSize,
                                    const uint8_t* content,
                                    lurFilesDescriptionHeader_t filesList[],
                                    uint16_t* noOfFiles)
{
    /* uint32_t declaredFileLength; */
    /* memcpy(&declaredFileLength, content, sizeof(uint32_t)); */
    /* declaredFileLength = ntohl(declaredFileLength); */

    /* if (declaredFileLength != fileSize) */
    /* { */
    /* 	return ARINC_ERR_MALFORMED_PKT; */
    /* } */

    memcpy(noOfFiles, content + 6, sizeof(uint16_t));
    *noOfFiles = ntohs(*noOfFiles);

    if (*noOfFiles > MAX_FILE_PER_TRANSFER)
    {
        return ARINC_ERR_FILES_LIST_TOO_LARGE;
    }

    uint8_t offset = 8; // pula o header

    for (int i = 0; i < *noOfFiles; i++)
    {
        memcpy(&filesList[i].headerFileNameLength,
               content + offset,
               sizeof(uint8_t));
	printf("\n\n %d", filesList[i].headerFileNameLength);

        offset++;

        strncpy(filesList[i].headerFileName,
                (char*)content + offset,
                MAX_DESCRIPTION_LEN - 1);
        filesList[i].headerFileName[MAX_DESCRIPTION_LEN] = '\0';

	printf("\n\n\n %s", filesList[i].headerFileName);

        offset += filesList[i].headerFileNameLength; // null byte

        memcpy(&filesList[i].loadPartNumberNameLength,
               content + offset,
               sizeof(uint8_t));

	printf("\n\n %d", filesList[i].loadPartNumberNameLength);
	

        offset++;

        strncpy(filesList[i].loadPartNumberName,
                (char*)content + offset,
                MAX_DESCRIPTION_LEN - 1);
        filesList[i].loadPartNumberName[MAX_DESCRIPTION_LEN] = '\0';

        ESP_LOGI(TAG, "header file name: %s", filesList[i].headerFileName);
        ESP_LOGI(
            TAG, "load part number name: %s", filesList[i].loadPartNumberName);
    }

    return ARINC_ERR_OK;
}

arincErr_t
genLoadUploadingStatus(ARINC_STATUS_CODE_t uploadOperationStatusCode,
                       uint8_t uploadStatusDescriptionLength,
                       const char* uploadStatusDescription, // Usar const char*
                       uint16_t counter,
                       uint16_t exceptionTimer,
                       uint16_t numberOfHeaderFiles,
                       arincStatusFileScheme_t* files,
                       uint8_t* arincDataBuffer,
                       size_t maxBufferSize, // Não usado
                       size_t* bytesWritten)
{
    // O offset começa APÓS o campo de Length (4 bytes), que será preenchido no final.
    size_t currentOffset = sizeof(uint32_t); // Começa em 4

    // Variáveis que precisam ser definidas no seu código globalmente:
    // extern const uint8_t protocolVersion[2];
    // extern const size_t MAX_DESCRIPTION_LEN;

    // --- 1. Serialização do Status Header de Comprimento Variável ---

    // A) Campos Fixos do Header
    // 1. protocolVersion (2 bytes)
    if (currentOffset + 2 > maxBufferSize) return ARINC_ERR_NO_MEM;
    memcpy(arincDataBuffer + currentOffset, protocolVersion, 2);
    currentOffset += 2;

    // 2. uploadOperationStatusCode (1 byte)
    if (currentOffset + 1 > maxBufferSize) return ARINC_ERR_NO_MEM;
    arincDataBuffer[currentOffset++] = (uint8_t)uploadOperationStatusCode;

    // 3. uploadStatusDescriptionLength (1 byte)
    if (currentOffset + 1 > maxBufferSize) return ARINC_ERR_NO_MEM;
    arincDataBuffer[currentOffset++] = uploadStatusDescriptionLength;

    // 4. counter (2 bytes, Big Endian)
    if (currentOffset + 2 > maxBufferSize) return ARINC_ERR_NO_MEM;
    uint16_t net_counter = htons(counter);
    memcpy(arincDataBuffer + currentOffset, &net_counter, sizeof(uint16_t));
    currentOffset += sizeof(uint16_t);

    // 5. exceptionTimer (2 bytes, Big Endian)
    if (currentOffset + 2 > maxBufferSize) return ARINC_ERR_NO_MEM;
    uint16_t net_exceptionTimer = htons(exceptionTimer);
    memcpy(arincDataBuffer + currentOffset, &net_exceptionTimer, sizeof(uint16_t));
    currentOffset += sizeof(uint16_t);

    // 6. numberOfHeaderFiles (2 bytes, Big Endian)
    if (currentOffset + 2 > maxBufferSize) return ARINC_ERR_NO_MEM;
    uint16_t net_numberOfHeaderFiles = htons(numberOfHeaderFiles);
    memcpy(arincDataBuffer + currentOffset, &net_numberOfHeaderFiles, sizeof(uint16_t));
    currentOffset += sizeof(uint16_t);

    // B) Dados Variáveis do Header
    // 7. uploadStatusDescription (uploadStatusDescriptionLength bytes)
    if (currentOffset + uploadStatusDescriptionLength > maxBufferSize) return ARINC_ERR_NO_MEM;
    memcpy(arincDataBuffer + currentOffset, uploadStatusDescription, uploadStatusDescriptionLength);
    currentOffset += uploadStatusDescriptionLength;


    // --- 2. Serialização dos Itens de Arquivo (Files) ---
    for (int i = 0; i < numberOfHeaderFiles; i++)
    {
	const arincStatusFileScheme_t *file = &files[i];

        // 1. headerFileIdentifier (4 bytes, Big Endian)
        /* if (currentOffset + 4 > maxBufferSize) return ARINC_ERR_NO_MEM; */
        /* uint32_t net_headerFileIdentifier = htonl(file->headerFileIdentifier); */
        /* memcpy(arincDataBuffer + currentOffset, &net_headerFileIdentifier, sizeof(uint32_t)); */
        /* currentOffset += sizeof(uint32_t); */

        // 2. headerFileNameLength (1 byte) e headerFileName (Variável)
        size_t file_name_size = 1 + file->headerFileNameLength;
        if (currentOffset + file_name_size > maxBufferSize) return ARINC_ERR_NO_MEM;
        arincDataBuffer[currentOffset++] = file->headerFileNameLength;
        memcpy(arincDataBuffer + currentOffset, file->headerFileName, file->headerFileNameLength);
        currentOffset += file->headerFileNameLength;

        // 3. loadPartNumberLength (1 byte) e loadPartNumber (Variável)
        size_t part_num_size = 1 + file->loadPartNumberLength;
        if (currentOffset + part_num_size > maxBufferSize) return ARINC_ERR_NO_MEM;
        arincDataBuffer[currentOffset++] = file->loadPartNumberLength;
        memcpy(arincDataBuffer + currentOffset, file->loadPartNumber, file->loadPartNumberLength);
        currentOffset += file->loadPartNumberLength;

        // 4. loadStatusDescriptionLength (1 byte) e loadStatusDescription (Variável)
        size_t desc_size = 1 + file->loadStatusDescriptionLength;
        if (currentOffset + desc_size > maxBufferSize) return ARINC_ERR_NO_MEM;
        arincDataBuffer[currentOffset++] = file->loadStatusDescriptionLength;
        memcpy(arincDataBuffer + currentOffset, file->loadStatusDescription, file->loadStatusDescriptionLength);
        currentOffset += file->loadStatusDescriptionLength;

        // 5. loadStatusCode (1 byte)
        if (currentOffset + 1 > maxBufferSize) return ARINC_ERR_NO_MEM;
        arincDataBuffer[currentOffset++] = (uint8_t)file->loadStatus;

        // 6. loadStatusCounter (3 bytes + NULL, char)
        if (currentOffset + 4 > maxBufferSize) return ARINC_ERR_NO_MEM;
        memcpy(arincDataBuffer + currentOffset, (uint8_t*) file->loadRatio, 3);

        currentOffset += 3;

	arincDataBuffer[currentOffset] = '\0';
	currentOffset += 1;
    }

    // --- 3. Preenchimento do Campo Length (Primeiros 4 bytes) ---

    // O comprimento final é o offset atual menos os 4 bytes do próprio campo Length.
    uint32_t finalFileLength = (uint32_t)(currentOffset - sizeof(uint32_t));
    uint32_t network_fileLength = htonl(finalFileLength);
    
    // Escreve o comprimento total (Big Endian) no início do buffer (offset 0)
    memcpy(arincDataBuffer, &network_fileLength, sizeof(uint32_t));
    
    // Define o número de bytes escritos
    if (bytesWritten) {
        *bytesWritten = currentOffset;
    }

    return ARINC_ERR_OK;
}

arincErr_t arincValidateFileAndGetName(const char* filename,
                                       ARINC_DATA_TYPE_t out
                                       __attribute__((unused)))
{
    ESP_LOGW(TAG, "validating file name and type");
    if (strstr(filename, DEVICE_PN) == NULL)
    {
        ESP_LOGE(TAG, "unauthorized file type");
        return ARINC_ERR_UNAUTH_DEVICE;
    }

    char* isLuiFile = strstr(filename, ".LUI");
    if (isLuiFile != NULL)
    {
        ESP_LOGI(TAG, "received LUI request");
        out = LUS;
    }
    else if (strstr(filename, ".LUR") != NULL)
    {
        out = LUR;
    }
    else
    {
    }
    return ARINC_ERR_OK;
}

void arinc_reset_buffer(void)
{
    if (xSemaphoreTake(arincBufferSemaphoreHandle, portMAX_DELAY) == pdTRUE)
    {
        arincDataBufferOffset = 0;
        xSemaphoreGive(arincBufferSemaphoreHandle);
    }
}

arincErr_t arinc_append_data(const uint8_t* data, size_t len)
{
    arincErr_t ret = ARINC_ERR_OK;

    if (xSemaphoreTake(arincBufferSemaphoreHandle, portMAX_DELAY) == pdTRUE)
    {
        if ((arincDataBufferOffset + len) > MAX_BUFFER_LEN)
        {
            ESP_LOGE(TAG,
                     "Buffer ARINC cheio! Cursor: %d, Novo dado: %d",
                     (int)arincDataBufferOffset,
                     (int)len);
            ret = ARINC_ERR_NO_MEM;
        }
        else
        {
            memcpy(arincDataBuffer + arincDataBufferOffset, data, len);

            arincDataBufferOffset += len;
        }

        xSemaphoreGive(arincBufferSemaphoreHandle);
    }
    else
    {
        ret = ARINC_ERR_UNKNOWN;
    }

    return ret;
}

void arinc_get_raw_buffer(const uint8_t** outPtr, size_t* outSize)
{
    *outPtr = arincDataBuffer;
    *outSize = arincDataBufferOffset;
}
