#include "arinc_core.h"
#include "arinc_file_schemes.h"

#include <string.h>


/*
  DEFINITIONS
 */
const uint8_t protocolVersion[2] = { 0x41, 0x34 }; // version A4

/* ----- PRIVATE FUNCIONS ----- */

/*
  Used only to initialize an information operation (file type LCI)
*/
arincErr_t *loadConigurationInitialization(ARINC_STATUS_CODE_t opStatusCode, arincConfigDataScheme_t* out);

/*
  Configuration of the target, it gives the list of the PNs in the target (file type LCL)
*/
arincErr_t *loadConfigurationList();

/*
  Progress and status of the information process (file type LCS)
*/
arincErr_t *loadConfigurationStatus();

/*
  Used ony to initialize an opload operation (LUI)
*/
arincErr_t *loadUploadingInitialization();

/*
  Progress and status of the uploading process (LUS)
*/
arincErr_t *loadUploadingStatus();

/*
  Used only to initialize a downloading operation (LND)
*/
arincErr_t *loadDownloadingMedia();

/*
  Progress of the downloading process (LNS)
*/
arincErr_t *loadDownloadingStatus();

/*
  Used only to initialize a downloading operation (LNO)
*/
arincErr_t *loadDownloadingOperator();

/*
  Used to give the list of files which are selected by the operator and are to be downloaded (LNA)
*/
arincErr_t* loadDownloadingList();
/* ---------------------------- */

/*
  definition of public functions
 */
/* arincErr_t arincGenerateFile(ARINC_DATA_TYPE_t fileType, */
/* 			     arincPayload_t* payload, arincFile_t* out) */
/* { */
  
/* } */


/*
  definition of private functions
 */
arincErr_t *loadConigurationInitialization(ARINC_STATUS_CODE_t opStatusCode, arincConfigDataScheme_t* out)
{
  memcpy(protocolVersion, out->protocolVersion, sizeof(out->protocolVersion));
  out->opAcceptanceStatusCode = opStatusCode;
  out->statusDescriptionLength = 0;
  out->statusDescription = NULL;

  return ARINC_ERR_OK;
}
