# Core

Este componente é o centro da arquitetura e contém a lógica de negócio pura da aplicação. Ele define os Modelos de Domínio (as structs e typedefs) e os Serviços de Domínio (as funções puras de regras de negócio).

O código aqui é 100% agnóstico de plataforma e infraestrutura. Ele não sabe o que é WiFi, FreeRTOS, SPIFFS ou HTTP.

## Princípios

- Pureza: O código deve ser C/C++ puro. NENHUM `#include` de drivers do ESP-IDF (`driver/`, `esp_http_client`, etc.), FreeRTOS (freertos/) ou qualquer biblioteca de infraestrutura é permitido.

- Dependência Interna: Este componente é o mais interno do hexágono. Ele não depende de nenhum outro componente da aplicação (nem ports, adapters ou core_fsm). Todos os outros componentes dependem dele.

- Testabilidade: Toda a lógica aqui deve ser compilável e testável em um host (PC) sem a necessidade de um ESP32.

## Exemplo de estrutura

Este componente deve ser organizado em "módulos" de domínio, onde cada módulo é responsável por uma área de negócio específica.

- protocol_core/ 
	- Responsabilidade: Lógica pura de formatação e parsing do protocolo ARINC.
	- Exemplo: `arinc_build_file(data_t* data, buffer_t* out_buffer)`.

- sensor_core/
  - Responsabilidade: Lógica pura de validação, calibragem ou processamento de dados de sensores.
  - Exemplo: `sensor_validate_reading(raw_data_t* raw, sensor_reading_t* out_reading)`.

- config_domain/
  - Responsabilidade: Modelos e regras de validação para a configuração do dispositivo.
  - Exemplo: `config_is_valid(device_config_t* config)`.

## Relação com Outros Componentes

- core_fsm (Aplicação): A máquina de estados usa este componente. Ela chama funções daqui (ex: arinc_build_file()) para executar lógica de negócio e tomar decisões.

- ports: As interfaces definidas nas portas usam os modelos de domínio definidos aqui em suas assinaturas de função (ex: `bool save_config(const device_config_t* config)`;).
