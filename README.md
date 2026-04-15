# ai-mcp-agent-orchestrator

Projeto de orquestracao de agentes de IA integrados a servidores MCP locais para executar tarefas envolvendo Gmail, Google Sheets, Monday e Azure AI/OpenAI.

## Visao Geral

O repositorio organiza um experimento de agentes especializados que compartilham um cliente de modelo e se conectam a ferramentas externas por meio de servidores MCP.

O objetivo e demonstrar:

- composicao de agentes com responsabilidades distintas;
- uso de um cliente de LLM centralizado;
- integracao com ferramentas via MCP;
- separacao entre codigo, configuracao e credenciais;
- fluxo local de automacao assistida por IA.

## Estrutura

- `main.py`: ponto de entrada do orquestrador.
- `agent/`: definicoes dos agentes especializados.
- `model/`: configuracao do cliente de modelo.
- `mcp_servers/`: servidores MCP locais para ferramentas externas.
- `.env.example`: variaveis esperadas para configuracao local.
- `requirements.txt`: dependencias Python.

## Configuracao

Crie um arquivo `.env` local com base em `.env.example`.

Variaveis esperadas incluem configuracoes para:

- Azure OpenAI;
- Azure AI Project;
- Monday;
- caminhos locais de credenciais OAuth quando necessario.

Arquivos reais de segredo, como `.env`, `credentials.json` e `token.json`, nao devem ser versionados.

## Gmail e Google Sheets

As integracoes com Gmail e Sheets usam OAuth 2.0. O fluxo esperado e manter localmente:

- `credentials.json`: credenciais do app Google Cloud;
- `token.json`: token gerado apos autorizacao do usuario.

Esses arquivos estao protegidos pelo `.gitignore` e nao fazem parte do repositorio.

## Como Executar

Instale as dependencias:

```bash
pip install -r requirements.txt
```

Configure o `.env` e os arquivos OAuth locais, quando aplicavel.

Execute o orquestrador:

```bash
python main.py
```

## Seguranca

A versao publicada foi curada para remover credenciais, tokens, ambientes virtuais, caches e repositorios terceiros vendorizados. Mesmo assim, se credenciais reais ja existiram no diretorio original, recomenda-se rotaciona-las antes de qualquer uso publico.

## Escopo

Este repositorio e um prototipo local de arquitetura multiagente. Para producao, ainda seriam necessarios testes, observabilidade, controle de permissoes, validacao de ferramentas e tratamento robusto de erros.
