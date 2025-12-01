#include <stddef.h>
#include <stdint.h>
#include <stdio.h>
#include "hashing.h"

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

    //size_t fileLen = getFileSize() - 40 - 32;
    int fileLen = 1024000;

    if (fseek(recFile, 40, SEEK_SET) != 0)
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

    uint8_t receivedHash[33];
    fseek(recFile, -32, SEEK_END);
    fread(receivedHash, 1, 32, recFile);
    receivedHash[33] = '\0';

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
    fclose(recFile);

    return ESP_OK;
}  

#ifdef DEBUG
void func() 
{
    const char *filepath = "/spiffs/my_file.txt";
    FILE* f = fopen(filepath, "r");
    if (f == NULL) {
        ESP_LOGI(TAG, "File not found. Creating a dummy file...");
        f = fopen(filepath, "w");
        if (f == NULL) {
            ESP_LOGE(TAG, "Failed to create dummy file.");
            return;
        }
        fprintf(f, "Teste");
        fclose(f);
    } else {
        ESP_LOGI(TAG, "Found existing file.");
        fclose(f);
    }

    const uint8_t hash[32] = {
    0x89, 0xf3, 0x08, 0x21, 0x0c, 0x7c, 0x78, 0x20,
    0xba, 0xd0, 0x97, 0x4f, 0x31, 0xe7, 0x51, 0xbf,
    0xa4, 0x33, 0xd2, 0x06, 0x6a, 0x93, 0xe8, 0x08,
    0x94, 0x7c, 0x31, 0x88, 0xde, 0xdb, 0xa6, 0xe3
    };

    if (verifyFileIntegrity(filepath, hash))
    {
        ESP_LOGW("TESTE", "Hash ok");
    }
    else
    {
        ESP_LOGW("TESTE", "Hash not ok");
    }
}
#endif
