#ifndef FLASH_STORAGE_H
#define FLASH_STORAGE_H

#include <stdint.h>
#include <stddef.h>
#include "esp_err.h"

// Configuração da Partição (Defina isso no seu partitions.csv, ex: "storage")
#define STORAGE_PARTITION_LABEL "storage"

typedef struct {
    const void* partition; // esp_partition_t* (Oculto para encapsulamento)
    size_t offset;         // Cursor atual de escrita/leitura
    size_t total_size;     // Tamanho total (para leitura)
} FlashHandle_t;

/**
 * @brief Prepara a flash para escrita (Apaga o setor necessário).
 * @param total_expected_size Tamanho estimado (para apagar o espaço correto).
 */
esp_err_t flash_open_write(FlashHandle_t* handle, size_t total_expected_size);

/**
 * @brief Escreve um chunk de dados na flash.
 */
esp_err_t flash_write_chunk(FlashHandle_t* handle, const uint8_t* data, size_t len);

/**
 * @brief Prepara a flash para leitura.
 */
esp_err_t flash_open_read(FlashHandle_t* handle, size_t* out_total_size);

/**
 * @brief Lê um chunk da flash.
 */
esp_err_t flash_read_chunk(FlashHandle_t* handle, uint8_t* dest, size_t len);

void flash_close(FlashHandle_t* handle);

#endif
