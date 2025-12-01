#include "storage_port.h"

void storageInit()
{
    partitionSetup();
    initLogFile();
    return;
}