#include <stddef.h>
#include <stdint.h>
#include <stdio.h>
#include "hashing.h"
#include "tftp_client.h"

static const char* TAG = "SHA-256";

esp_err_t verifyFileIntegrity(char* filepath)
{
    FILE* recFile = fopen(filepath, "rb");
    if (recFile == NULL)
    {
        ESP_LOGE(TAG, "Failed to open given file: %s", filepath);
        return ESP_FAIL;
    }

    mbedtls_sha256_context ctx;

    uint8_t* buf = (uint8_t*) malloc(READ_BUFFER_SIZE);
    /* uint8_t buf[READ_BUFFER_SIZE]; */
    if (!buf)
    {
        ESP_LOGE(TAG, "Failed to allocate memory for read buffer");
        fclose(recFile);
        return ESP_FAIL;
    }

    mbedtls_sha256_init(&ctx);
    int mbed_r = mbedtls_sha256_starts(&ctx, 0);

    size_t fileLen = getImageFileSize() - PN_BYTES - SHA256_HASH_LEN;
    
    if (fseek(recFile, PN_BYTES, SEEK_SET) != 0)
    {
        ESP_LOGE(TAG, "Error seeking in file");
        fclose(recFile);
        free(buf);
        return ESP_FAIL;
    }

    size_t bytes_read = 1;
    while (bytes_read > 0 && fileLen > 0)
    {
        if (READ_BUFFER_SIZE <= fileLen)
        {
            bytes_read = fread(buf, 1, READ_BUFFER_SIZE, recFile);
            fileLen -= READ_BUFFER_SIZE;
        }
        else
        {
            memset(buf, 0, READ_BUFFER_SIZE);
            bytes_read = fread(buf, 1, fileLen, recFile);
            fileLen -= fileLen;
        }
        
        if (bytes_read > 0)
        {   
            mbed_r = mbedtls_sha256_update(&ctx, buf, bytes_read);
            if (mbed_r != 0)
            {
                ESP_LOGE(TAG,
                        "Failed to update SHA256 context, error: %d",
                        mbed_r);
                fclose(recFile);
                free(buf);
                return ESP_FAIL;
            }
        }
        else
        {
            bytes_read = 0;
        }
    }
    free(buf);

    uint8_t receivedHash[SHA256_HASH_LEN + 1];
    fseek(recFile, -SHA256_HASH_LEN, SEEK_END);
    fread(receivedHash, 1, SHA256_HASH_LEN, recFile);
    receivedHash[SHA256_HASH_LEN] = '\0';

    fclose(recFile);

    uint8_t shaResult[SHA256_HASH_LEN];
    mbed_r = mbedtls_sha256_finish(&ctx, shaResult);

    if (memcmp(shaResult, receivedHash, SHA256_HASH_LEN) != 0)
    {
        mbedtls_sha256_free(&ctx);
        ESP_LOGW(TAG, "File integrity violated, no match");
        return ESP_FAIL;
    }

    char hashStr[SHA256_HASH_LEN * 2 + 1];
    char recHashStr[SHA256_HASH_LEN * 2 + 1];
    for (int i = 0; i < SHA256_HASH_LEN; i++)
    {
        sprintf(&hashStr[i*2], "%02x", shaResult[i]);
        sprintf(&recHashStr[i*2], "%02x", receivedHash[i]);
    }
    hashStr[SHA256_HASH_LEN*2] = '\0';
    ESP_LOGI(TAG, "Hash result: %s", hashStr);
    ESP_LOGI(TAG, "Received hash: %s", recHashStr);

    ESP_LOGI(TAG, "File integrity is fine");

    mbedtls_sha256_free(&ctx);

    return ESP_OK;
}  
