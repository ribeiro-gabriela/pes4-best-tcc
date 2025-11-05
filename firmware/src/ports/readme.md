# Ports

Este componente define os contratos (interfaces) que separam a camada de Aplicação (core_fsm) da camada de Infraestrutura (adapters).

Elas definem o que a aplicação pode fazer (API) e o que ela precisa (dependências de infra), mas nunca como isso é feito. Este diretório deve conter majoritariamente arquivos .h.

## Princípios

- Abstração: as Portas são as "tomadas" (interfaces). Elas permitem que diferentes "plugs" (adaptadores) sejam conectados sem que o "aparelho" (a FSM) precise mudar.
- Inversão de Dependência: Este é o componente-chave para a Inversão de Dependência. Tanto a FSM (core_fsm) quanto os adapters dependem das ports. A FSM depende delas para chamar as interfaces, e os adapters dependem delas para implementar as interfaces.
- Sem Implementação: Os arquivos aqui não devem conter lógica, apenas as assinaturas das funções ou structs com ponteiros de função que definem o contrato.

## Tipos de Portas

Este componente define dois tipos de fronteiras para o hexágono:

1. Portas Primárias (Driving Ports / API da Aplicação)

Definem como o "mundo exterior" (adaptadores) chama a nossa aplicação. Elas são a API do core_fsm.
- Implementadas por: core_fsm ou services (Serviços de Aplicação).
- Chamadas por: Adaptadores Primários (ex: adapter_http_server, adapter_ble_service).

    Exemplo: port_command_api.h
```c
// Um adaptador HTTP pode chamar esta função ao receber um POST
void api_processar_comando_remoto(const char* comando_json);
```

2. Portas Secundárias (Driven Ports / Repositórios)

Definem o que a nossa aplicação precisa que o "mundo exterior" (adaptadores) forneça. São as "tomadas" onde plugamos os drivers.
- Implementadas por: Adaptadores Secundários (ex: adapter_spiffs_storage, adapter_http_client).
- Chamadas por: core_fsm.

    Exemplo: port_storage.h
```c
// A FSM chama esta função, sem saber que é o SPIFFS que está salvando
bool port_storage_save_file(const char* path, const uint8_t* data, size_t len);
```

	Exemplo: port_arinc_writer.h
```c
// A FSM chama esta função para enviar um arquivo ARINC, sem saber que é por TFTP
bool port_arinc_send_file(const char* filename, const buffer_t* file_content);
```

## Regra de Dependência

DEPENDE DE (Aponta para Dentro):
	- `components/core_domain`: Para usar os modelos de dados e entidades nas assinaturas das funções (ex: `bool publish(const sensor_reading_t* data)`;).

NÃO DEPENDE DE:
	- `core_fsm`, adapters, `main`. As Portas são puramente definições e não dependem de quem as usa ou implementa.
