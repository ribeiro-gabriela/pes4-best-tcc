#include <stdio.h>
#include <dirent.h>
#include "esp_log.h"
#include "cli.h"
#include "cli_register_commands.h"

#define PROMPT_STR "BC"

// [BST-441, BST-635]
esp_err_t initConsole()
{
    esp_console_repl_t *repl = NULL;

    esp_console_repl_config_t repl_config = ESP_CONSOLE_REPL_CONFIG_DEFAULT();
    esp_console_dev_uart_config_t hw_config = ESP_CONSOLE_DEV_UART_CONFIG_DEFAULT();
   
    // Prompt to be printed before each line.
    repl_config.prompt = PROMPT_STR ">";
    repl_config.max_cmdline_length = 4096;

    // Register commands 
    registerRestart();
    registerLs();
    registerVerifySHA();
    registerParkingBrake();
    registerWeightOnWheels();
    registerMaintenanceMode();
    
    #ifdef TEST_COMMAND_ENABLED
    registerTest();
    #endif
    
    // BST-441
    esp_console_register_help_command();

    ESP_ERROR_CHECK(esp_console_new_repl_uart(&hw_config, &repl_config, &repl));
    ESP_ERROR_CHECK(esp_console_start_repl(repl));

    return ESP_OK;
}

esp_err_t registerLog()
{
    FILE* logFile = fopen("/spiffs/log.txt", "a");
    if (logFile == NULL)
    {
        ESP_LOGE("CLI", "Failed to open log file for appending");
        return ESP_FAIL;
    }

    // Escrever mensagem de log no arquivo
    return ESP_OK;
}