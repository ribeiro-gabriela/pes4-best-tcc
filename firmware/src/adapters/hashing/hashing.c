#include <stdio.h>
#include "hashing.h"

static const char* TAG = "SHA-256";

bool verify_file_integrity(const char* filepath, uint8_t* received_hash)
{
    FILE* rec_file = fopen(filepath, "rb");
    if (rec_file == NULL)
    {
        ESP_LOGE(TAG, "Failed to open given file: %s", filepath);
        return false;
    }

    mbedtls_sha256_context ctx;
    esp_err_t esp_ret;

    uint8_t* buf = (uint8_t*) malloc(READ_BUFFER_SIZE);
    if (!buf)
    {
        ESP_LOGE(TAG, "Failed to allocate memory for read buffer");
        fclose(rec_file);
        return false;
    }

    mbedtls_sha256_init(&ctx);
    int mbed_r = mbedtls_sha256_starts(&ctx, 0);

    size_t bytes_read = 1;
    while (bytes_read > 0) 
    {
        bytes_read = fread(buf, 1, READ_BUFFER_SIZE, rec_file);
        if (bytes_read > 0)
        {
            mbed_r = mbedtls_sha256_update(&ctx, buf, bytes_read);
            if (mbed_r != 0)
            {
                ESP_LOGE(TAG, "Failed to update SHA256 context, error: %d", mbed_r);
                fclose(rec_file);
                free(buf);
                return false;
            }
        }
    }
    fclose(rec_file);
    free(buf);

    uint8_t sha_result[SHA256_HASH_LEN];
    mbed_r = mbedtls_sha256_finish(&ctx, sha_result);

    if (memcmp(sha_result, received_hash, SHA256_HASH_LEN) != 0)
    {
        mbedtls_sha256_free(&ctx);
        ESP_LOGW(TAG, "File integrity violated, no match");
        return false;
    }

    char hash_str[SHA256_HASH_LEN * 2 + 1];
    char rec_hash_str[SHA256_HASH_LEN * 2 + 1];
    for (int i = 0; i < SHA256_HASH_LEN; i++)
    {
        sprintf(&hash_str[i*2], "%02x", sha_result[i]);
        sprintf(&rec_hash_str[i*2], "%02x", received_hash[i]);
    }
    hash_str[SHA256_HASH_LEN*2] = '\0';
    ESP_LOGI(TAG, "Hash result: %s", hash_str);
    ESP_LOGI(TAG, "Received hash: %s", rec_hash_str);

    ESP_LOGI(TAG, "File integrity is fine");

    mbedtls_sha256_free(&ctx);

    return true;
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

    if (verify_file_integrity(filepath, hash))
    {
        ESP_LOGW("TESTE", "Hash ok");
    }
    else
    {
        ESP_LOGW("TESTE", "Hash not ok");
    }
}
#endif
