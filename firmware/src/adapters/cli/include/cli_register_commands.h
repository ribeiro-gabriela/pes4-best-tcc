#include "esp_console.h"
#include "cli_commands_handler.h"

void register_restart(void)
{
    const esp_console_cmd_t cmd = {
        .command = "restart",
        .help = "Soft restart BC system",
        .hint = NULL,
        .func = &restartHandler
    };
    ESP_ERROR_CHECK(esp_console_cmd_register(&cmd));
}

void register_ls(void)
{
    const esp_console_cmd_t cmd = {
        .command = "ls",
        .help = "List directories and files in the current partition",
        .hint = NULL,
        .func = &lsHandler
    };
    ESP_ERROR_CHECK(esp_console_cmd_register(&cmd));
}

void register_verify_sha(void)
{
    const esp_console_cmd_t cmd = {
        .command = "versha",
        .help = "Verify given file location against given hash value",
        .hint = NULL,
        .func = &verifySHAHandler
    };
    ESP_ERROR_CHECK(esp_console_cmd_register(&cmd));
}

void register_maintenance_mode(void)
{
    const esp_console_cmd_t cmd = {
        .command = "mnt",
        .help = "Enable or disable aircraft maintenance mode",
        .hint = NULL,
        .func = &maintenanceModeHandler
    };
    ESP_ERROR_CHECK(esp_console_cmd_register(&cmd));
}