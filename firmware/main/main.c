#include "wifi_core.h"
#include "storage_core.h"
#include "https_port.h"
#include "hashing.h"
#include "cli.h"
#include "tftp.h"

void app_main(void)
{
    //Initialize NVS
    esp_err_t ret = nvs_flash_init();
    if (ret == ESP_ERR_NVS_NO_FREE_PAGES || ret == ESP_ERR_NVS_NEW_VERSION_FOUND)
    {
        ESP_ERROR_CHECK(nvs_flash_erase());
        ret = nvs_flash_init();
    }
    ESP_ERROR_CHECK(ret);

    partition_setup();

    wifi_init_softap();
    //init_https_server();

    init_console();

    struct tftp_server* server = tftp_server_create("/spiffs", 70);
    tftp_server_write_set(server, 1);
    tftp_server_run(server);

    #ifndef DEBUG
    func();
    #endif
}