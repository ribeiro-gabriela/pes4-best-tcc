#ifndef ARINC_ADAPTER__H
#define ARINC_ADAPTER__H

#include <stdlib.h>

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
  LCI,
  LCL,
  LCS,
  LUI,
  LUR,
  LUH,
  FILE,
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
  ARINC_ERR_UNKNOWN = -1,
} arincErr_t;

/* typedef struct arincErr */
/* { */
/*   arincErrType_t errType; */
/*   char* info; */
/* } arincErr_t; */

/*
  @brief Generates an ARINC file to send via TFTP

 @param fileType the type of file to be generated
 @param payload data to be inserted on generated file
 @param out pointer to output buffer
*/
arincErr_t arincAdapterGenerateFile(ARINC_DATA_TYPE_t fileType,
				    arincPayload_t* payload, arincFile_t* out);




#endif
