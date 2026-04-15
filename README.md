# AI MCP Agent Orchestrator

Sistema multiagente com FastAPI, AutoGen e MCP para orquestrar operacoes entre Gmail, Google Sheets, Monday.com e analise assistida por Azure AI.

## O que o projeto faz

- recebe mensagens por WebSocket
- distribui tarefas entre agentes especializados
- integra Gmail e Google Sheets via MCP servers locais
- integra Monday.com via MCP server Node
- oferece analise e sugestao de graficos com Azure AI

## Estrutura

- `main.py`: servidor FastAPI e orquestracao principal dos agentes
- `agent/`: agentes especializados
- `mcp_servers/gmail`: MCP server local para Gmail
- `mcp_servers/sheets`: MCP server local para Google Sheets
- `model/model.py`: configuracao do cliente de modelo

## Seguranca e curadoria

Esta versao foi preparada para publicacao:

- credenciais, tokens e arquivos `.env` foram removidos
- caminhos absolutos locais foram substituidos por caminhos relativos
- ambientes virtuais, caches, artefatos de IDE e repositorios aninhados foram excluidos
- o servidor vendorizado `mcp-brasil` nao foi incluido

## Configuracao

1. Crie um ambiente virtual.
2. Instale as dependencias de `requirements.txt`.
3. Copie `.env.example` para `.env` e preencha as variaveis necessarias.
4. Adicione seus arquivos `credentials.json` e autentique os MCP servers de Gmail e Sheets localmente.

## Execucao

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app_ws --reload
```

## Observacoes

- O projeto depende de servicos externos configurados corretamente.
- Os MCP servers de Gmail e Sheets exigem credenciais OAuth locais.
- O agente do Monday depende de `npx` e de um token valido no ambiente.
