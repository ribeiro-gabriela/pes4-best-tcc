# Adapters

Este componente é a camada mais externa da arquitetura. Ele contém todo o código de infraestrutura, específico da plataforma e dos drivers.

Os adaptadores são os "plugs" concretos que se conectam às "tomadas" abstratas (as ports). Seu trabalho principal é traduzir dados entre o formato do mundo real (ex: JSON, bytes de UART, pacotes TFTP) e os modelos de domínio puros (as structs do core_domain).

## Princípios
- Implementação de Portas: A principal responsabilidade dos adaptadores é implementar as interfaces definidas em components/ports/.
- Código de Plataforma: Este é o único lugar onde é permitido usar bibliotecas e drivers do ESP-IDF (ex: `driver/uart.h`, `esp_spiffs.h`, `esp_wifi.h`, `esp_http_client.h`), FreeRTOS (`freertos/`), ou bibliotecas de terceiros (ex: `cJSON`).
- Tradução: Os adaptadores traduzem os dados. Um `adapter_http_server` transforma uma string JSON em uma struct do domínio. Um `adapter_spiffs_storage` transforma uma struct do domínio em bytes para salvar em um arquivo.

## Tipos de Adaptadores

Assim como as Portas, existem dois tipos de Adaptadores:

### 1. Adaptadores Primários (Driving Adapters)

Iniciam a interação. Eles "dirigem" (chamam) a aplicação.
- O que fazem: Escutam eventos do mundo exterior (ex: um comando na UART, uma requisição HTTP, um evento WiFi) e chamam uma Porta Primária (API da aplicação).

**Exemplos:**
- `adapter_uart_listener`: Roda uma task que escuta a UART e chama `api_processar_comando_serial()` (Porta Primária) quando uma linha chega.
- `adapter_http_server`: Registra um endpoint HTTP que, ao ser chamado, parseia o corpo da requisição e chama `api_processar_comando_remoto()` (Porta Primária).
- `adapter_wifi_events`: Escuta eventos de conexão/desconexão do WiFi e chama `api_notificar_mudanca_status_wifi()` (Porta Primária).

### 2. Adaptadores Secundários (Driven Adapters)

São "dirigidos" (chamados) pela aplicação.

- O que fazem: Implementam as Portas Secundárias. A FSM chama a porta (port_storage_save_file()) e o sistema de build do ESP-IDF "injeta" a implementação deste adaptador.

**Exemplos:**
- `adapter_spiffs_storage`: Implementa as funções da `port_storage.h` (ex: `save_file`, `read_file`) usando as funções do `esp_spiffs.h`.
- `adapter_tftp_client` (ARINC): Implementa a `port_arinc_writer.h` (ex: `send_file`) estabelecendo uma conexão TFTP e enviando os bytes.
- `adapter_esp_logger`: Implementa a `port_logger.h` (ex: `log_info`) simplesmente chamando `ESP_LOGI()`.

## Regra de Dependência
- DEPENDE DE (Aponta para Dentro):
  - components/ports: Para saber quais interfaces devem implementar.
  - components/core_domain: Para saber quais modelos de dados devem traduzir.
  - Bibliotecas Externas: driver, freertos, esp_idf, etc.

NÃO DEPENDE DE (Nunca!):
	- `components/core_fsm`: Um adaptador nunca deve saber da existência da FSM, seus estados ou sua lógica interna. Ele só conhece a port que ele implementa ou chama.
