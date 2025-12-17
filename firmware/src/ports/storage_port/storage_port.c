#include "storage_port.h"
#include "storage_adapter.h"

void storageInit()
{
    partitionSetup();
    initLogFile();
    return;
}


void formatDataPartition()
{
  formatSpiffsData();
}
