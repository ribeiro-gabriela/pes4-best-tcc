#ifndef ARINC_ADAPTER__H
#define ARINC_ADAPTER__H

#include <stdlib.h>

#include "cc.h"

#include <stddef.h>
#include <stdint.h>
#include <string.h>
#include <sys/types.h>



#define MAX_DESCRIPTION_LEN 255
#define MAX_FILE_PER_TRANSFER 3
#    define MAX_PROTOCOL_FIELD_LENGTH 255

#    define MAX_LUR_SIZE (4 + 2 + 2 + 1 + 255 + 1 + 255)
#    define MAX_LUS_SIZE                                                       \
  ((4 + 2 + 2 + 1 + 255 + 2 + 2 + 2 + 3 + 2 + 1 + 255 + 1 + 255 + 3 + 2 + \
    1 + 255) * MAX_FILE_PER_TRANSFER)
#define MAX_LUI_FILE (4 + 2 + 2 + 1 + 255)

typedef enum ARINC_STATUS_CODE {
  ARINC_OPERATION_ACCEPTED = 0x0001,
  ARINC_OPERATION_NOT_ACCEPTED = 0x1000,
  ARINC_OPERATION_NOT_SUPPORTED = 0x1002,
  ARINC_OPERATION_IN_PROGRESS = 0x0002,
  ARINC_OP_COMPLETED_WITHOUT_ERROR = 0x0003,
  ARINC_OP_IN_PROGRESS_ADITIONAL_INFO_PROVIDED = 0x0004,
  ARINC_OP_ABORTED_BY_TARGET = 0x1003,
  ARINC_OP_ABORTED_BY_DATA_LOADER = 0x1004,
  ARINC_OP_ABORTED_BY_OPERATOR = 0x1005,
  ARINC_REQUIRED_DATA_ERROR = 0x1007
} ARINC_STATUS_CODE_t;

typedef uint8_t arincPayload_t;
typedef uint8_t arincFile_t;

typedef enum ARINC_DATA_TYPE {
  ARINC_NONE,
  LCI,
  LCL,
  LCS,
  LUI,
  LUR,
  LUH,
  ARINC_FILE,
  LUS,
  LND,
  LNR,
  LNS,
  LNO,
  LNL,
  LNA
} ARINC_DATA_TYPE_t;

typedef enum arincErrType
{
    ARINC_ERR_OK = 0,
    ARINC_ERR_NO_MEM = -1,
    ARINC_ERR_UNKNOWN = -2,
    ARINC_ERR_UNAUTH_DEVICE = -3,
    ARINC_ERR_INVALID_ARGS = -4,
    ARINC_ERR_MALFORMED_PKT = -5,
    ARINC_ERR_FILES_LIST_TOO_LARGE = -6
} arincErr_t;



#pragma pack(push, 1)
typedef struct arincConfigDataScheme
{
  uint32_t fileLength;
  uint8_t protocolVersion[2];
  ARINC_STATUS_CODE_t opAcceptanceStatusCode;
  uint8_t statusDescriptionLength;
  uint8_t* statusDescription;
} arincConfigDataScheme_t;
#pragma pack(pop)



#pragma pack(push, 1)
typedef struct loadUploadingRequestHeader
{
    uint32_t fileLength;
    uint16_t protocolVersion;
    uint8_t noOfHeaderFiles;
} loadUploadingRequestHeader_t;
#pragma pack(pop)

#pragma pack(push, 1)
typedef struct lurFileHeader
{
    uint8_t headerFileNameLength;
    char headerFileName[MAX_DESCRIPTION_LEN];
    uint8_t loadPartNumberNameLength;
    char loadPartNumberName[MAX_DESCRIPTION_LEN];
} lurFilesDescriptionHeader_t;
#pragma pack(pop)


#pragma pack(push,1)
typedef struct arincStatusScheme
{
    uint32_t fileLength;
    uint16_t protocolVersion;
    uint16_t uploadOperationStatusCode;
    uint8_t uploadStatusDescriptionLength;
    char uploadStatusDescription[MAX_DESCRIPTION_LEN];
    uint16_t counter;
    uint16_t exceptionTimer;
    uint16_t estimatedTime;
    char loadListRatio[3];
    uint16_t numberOfHeaderFiles;
} arincStatusScheme_t;
#pragma pack(pop)

#pragma pack(push,1)
typedef struct arincStatusFileScheme
{
    uint8_t headerFileNameLength;
    char headerFileName[MAX_DESCRIPTION_LEN];
    uint8_t loadPartNumberLength;
    char loadPartNumber[MAX_DESCRIPTION_LEN];
    char loadRatio[3];
    uint16_t loadStatus;
    uint8_t loadStatusDescriptionLength;
    char loadStatusDescription[MAX_DESCRIPTION_LEN];    
} arincStatusFileScheme_t;
#pragma pack(pop)

/*
  DEFINITIONS
 */

arincErr_t initArinc(void);
arincErr_t loadUploadingInitialization(ARINC_STATUS_CODE_t opStatusCode,
                                       uint8_t* description,
                                       uint8_t buf[MAX_LUI_FILE],
                                       size_t* bufSize);

arincErr_t readLoadUploadingRequest(size_t fileSize,
                                    const uint8_t* content,     // const para segurança
                                    lurFilesDescriptionHeader_t filesList[], 
                                    uint16_t* outParsedCount);

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
                       size_t* bytesWritten);

arincErr_t arincDataChunk(uint8_t* payload, size_t len);

arincErr_t arincValidateFileAndGetName(const char* filename, ARINC_DATA_TYPE_t out);
void arinc_reset_buffer(void);
arincErr_t arinc_append_data(const uint8_t* data, size_t len);
void arinc_get_raw_buffer(const uint8_t** outPtr, size_t* outSize);

#endif
