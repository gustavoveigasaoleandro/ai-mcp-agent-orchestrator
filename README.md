# ai-mcp-agent-orchestrator

Projeto de orquestração de agentes de IA integrados a servidores MCP locais para executar tarefas envolvendo Gmail, Google Sheets, Monday e Azure AI/OpenAI.

## Visão Geral

O repositório organiza um experimento de agentes especializados que compartilham um cliente de modelo e se conectam a ferramentas externas por meio de servidores MCP.

O objetivo é demonstrar:

- composição de agentes com responsabilidades distintas;
- uso de um cliente de LLM centralizado;
- integração com ferramentas via MCP;
- separação entre código, configuração e credenciais;
- fluxo local de automação assistida por IA.

## Estrutura

- `main.py`: ponto de entrada do orquestrador.
- `agent/`: definições dos agentes especializados.
- `model/`: configuração do cliente de modelo.
- `mcp_servers/`: servidores MCP locais para ferramentas externas.
- `.env.example`: variáveis esperadas para configuração local.
- `requirements.txt`: dependências Python.

## Configuração

Crie um arquivo `.env` local com base em `.env.example`.

Variáveis esperadas incluem configurações para:

- Azure OpenAI;
- Azure AI Project;
- Monday;
- caminhos locais de credenciais OAuth quando necessário.

Arquivos reais de segredo, como `.env`, `credentials.json` e `token.json`, não devem ser versionados.

## Gmail e Google Sheets

As integracoes com Gmail e Sheets usam OAuth 2.0. O fluxo esperado e manter localmente:

- `credentials.json`: credenciais do app Google Cloud;
- `token.json`: token gerado após autorização do usuário.

Esses arquivos estão protegidos pelo `.gitignore` e não fazem parte do repositório.

## Como Executar

Instale as dependências:

```bash
pip install -r requirements.txt
```

Configure o `.env` e os arquivos OAuth locais, quando aplicável.

Execute o orquestrador:

```bash
python main.py
```

## Segurança

A versão publicada foi curada para remover credenciais, tokens, ambientes virtuais, caches e repositórios terceiros vendorizados. Mesmo assim, se credenciais reais ja existiram no diretório original, recomenda-se rotaciona-las antes de qualquer uso público.

## Escopo

Este repositório e um protótipo local de arquitetura multiagente. Para produção, ainda seriam necessários testes, observabilidade, controle de permissões, validação de ferramentas e tratamento robusto de erros.
