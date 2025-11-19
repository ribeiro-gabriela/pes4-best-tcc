#ifndef CLI_REGISTER_COMMANDS_H
#define CLI_REGISTER_COMMANDS_H

#include "esp_console.h"
#include "cli_commands_handler.h"

void registerRestart(void)
{
    const esp_console_cmd_t cmd = {
        .command = "restart",
        .help = "Soft restart BC system",
        .hint = NULL,
        .func = &restartHandler
    };
    ESP_ERROR_CHECK(esp_console_cmd_register(&cmd));
}

void registerLs(void)
{
    const esp_console_cmd_t cmd = {
        .command = "ls",
        .help = "List directories and files in the current partition",
        .hint = NULL,
        .func = &lsHandler
    };
    ESP_ERROR_CHECK(esp_console_cmd_register(&cmd));
}

void registerVerifySHA(void)
{
    const esp_console_cmd_t cmd = {
        .command = "versha",
        .help = "Verify given file location against given hash value",
        .hint = NULL,
        .func = &verifySHAHandler
    };
    ESP_ERROR_CHECK(esp_console_cmd_register(&cmd));
}

void registerParkingBrake(void)
{
    const esp_console_cmd_t cmd = {
        .command = "pb",
        .help = "<enable> or <disable> parking brake sensor",
        .hint = NULL,
        .func = &parkingBrakeHandler
    };
    ESP_ERROR_CHECK(esp_console_cmd_register(&cmd));
}

void registerWeightOnWheels(void)
{
    const esp_console_cmd_t cmd = {
        .command = "wow",
        .help = "<enable> or <disable> weight on wheels sensor",
        .hint = NULL,
        .func = &weightOnWheelsHandler
    };
    ESP_ERROR_CHECK(esp_console_cmd_register(&cmd));
}

void registerMaintenanceMode(void)
{
    const esp_console_cmd_t cmd = {
        .command = "mnt",
        .help = "<enable> or <disable> aircraft maintenance mode",
        .hint = NULL,
        .func = &maintenanceModeHandler
    };
    ESP_ERROR_CHECK(esp_console_cmd_register(&cmd));
}

#ifdef TEST_COMMAND_ENABLED
void registerTest(void)
{
    const esp_console_cmd_t cmd = {
        .command = "test",
        .help = "Test command for BC system queue state transitions and logging",
        .hint = NULL,
        .func = &testHandler
    };
    ESP_ERROR_CHECK(esp_console_cmd_register(&cmd));
}
#endif

#endif