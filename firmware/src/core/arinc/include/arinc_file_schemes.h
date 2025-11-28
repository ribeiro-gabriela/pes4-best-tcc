#ifndef ARINC_FILE_SCHEMES__H
#define ARINC_FILE_SCHEMES__H

#include <stdint.h>

#include "arinc_core.h"

#define MAX_PROTOCOL_FIELD_LENGTH 2040

typedef struct arincConfigDataScheme
{
  uint8_t protocolVersion[2];
  ARINC_STATUS_CODE_t opAcceptanceStatusCode;
  uint8_t statusDescriptionLength;
  uint8_t* statusDescription;
} arincConfigDataScheme_t;

#endif
