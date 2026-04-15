import asyncio
import warnings
import requests
import uuid
import datetime
# Removido 'from builtins import anext' pois não é necessário em Python 3.10+
# e pode causar problemas se não for o caso. O stream já é um async iterator.

# Supondo que essas importações funcionem no seu ambiente
from agent.gmail.agent import build_agent
from agent.sheets.agent import build_agent as build_sheets_agent
from agent.monday.agent import build_agent as build_monday_agent
from agent.userProxy.agent import build_agent as build_user_agent
from agent.AnalistAgent.agent import build_agent as build_analyst_agent
from agent.azureAiAgent.agent import graph_suggestion_agent
from autogen_agentchat.teams import SelectorGroupChat
from autogen_agentchat.conditions import TextMentionTermination
from model.model import model_client
from autogen_agentchat.teams._group_chat._events import GroupChatError

warnings.filterwarnings("ignore", message="FP16 is not supported on CPU; using FP32 instead")

def is_safe_input(prompt: str) -> bool:
    try:
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "llama-guard3",
                "prompt": prompt,
                "stream": False
            },
            timeout=10
        )
        result = response.json()
        output = result.get("response", "")
        return "unsafe" not in output.lower()
    except requests.exceptions.Timeout:
        print("⚠️ A verificação de segurança excedeu o tempo limite. Permitindo por padrão.")
        return True
    except Exception as e:
        print(f"Erro na verificação de segurança com llama-guard3: {e}")
        return True

AGENTS_META = [
    {
        "name": "User",
        "avatar": "👤",
        "description": "Você, o solicitante das ações."
    },
    {
        "name": "GmailAgent",
        "avatar": "📧",
        "description": "Extrai automaticamente dados de e-mails."
    },
    {
        "name": "SheetsAgent",
        "avatar": "📊",
        "description": "Registra e organiza os dados na planilha 'Registro de Solicitações - 2024'. Também fornece dados extraídos para outros agentes."
    },
    {
        "name": "MondayAgent",
        "avatar": "📅",
        "description": (
            "Você tem acesso ao quadro 'Solicitações de Compra' no Monday.com e é responsável por **todas as operações de um CRUD**:\n"
            "- 📥 Criar novas solicitações com base nos dados fornecidos.\n"
            "- 🔍 Consultar status, prazos, responsáveis ou comentários de solicitações já existentes.\n"
            "- ✏️ Atualizar qualquer campo ou progresso relacionado à solicitação.\n"
            "- 🗑️ Deletar solicitações quando explicitamente instruído.\n\n"
            "Você não é um agente exclusivo de registro — está autorizado a gerenciar o ciclo completo das solicitações conforme necessário."
        )
    },
    {
        "name": "graph_suggestion_agent",
        "avatar": "📈",
        "description": "Gera visualizações e análises gráficas com base em dados **explicitamente fornecidos** pelo UserProxyAgent ou SheetsAgent."
    },
    {
        "name": "AnalystAgent",
        "avatar": "🧠",
        "description": (
            "Fornece análises críticas, diagnósticos operacionais e recomendações estratégicas com base nos dados fornecidos pelos demais agentes. "
            "Também pode sugerir hipóteses e indicadores de performance relevantes para tomada de decisão."
        )
    },
    {
        "name": "UserProxyAgent",
        "avatar": "🤖",
        "description": "Interpreta comandos do usuário e organiza respostas com base nas interações com os demais agentes (Gmail, Sheets, Monday, Gráficos e Insights). Não realiza orquestração nem direcionamento entre agentes."
    },
    {
        "name": "AnalystAgent",
        "avatar": "🧠",
        "description": (
            "Fornece análises críticas, diagnósticos operacionais e recomendações estratégicas com base nos dados fornecidos pelos demais agentes. "
            "Também pode sugerir hipóteses e indicadores de performance relevantes para tomada de decisão. "
            "Sob hipótese nenhuma deve realizar qualquer ação sem a autorização explícita do usuário, especialmente no que se refere a diagnósticos ou recomendações automatizadas que impliquem ações operacionais."
        )
    }
]

selector_groupchat = None
agents = []

async def setup_agents():
    global agents, selector_groupchat
    gmail_agent = await build_agent()
    monday_agent = await build_monday_agent()
    sheets_agent = await build_sheets_agent()
    user_agent = await build_user_agent()
    analyst_agent = await build_analyst_agent()

    agents = [
        gmail_agent,
        monday_agent,
        sheets_agent,
        user_agent,
        graph_suggestion_agent,
        analyst_agent  # Novo agente de insights
    ]

    selector_prompt = """
        Você está em um sistema de agentes inteligentes que colaboram entre si para executar tarefas complexas.

        📦 Agentes disponíveis:
        - User → Você, o solicitante das ações.
        - GmailAgent → Extrai automaticamente dados de e-mails.
        - SheetsAgent → Registra e organiza os dados na planilha 'Registro de Solicitações - 2024'. Também fornece dados extraídos para outros agentes.
        - MondayAgent → Você tem acesso ao quadro "Solicitações de Compra" no Monday.com e é responsável por **todas as operações de um CRUD**:
          - 📥 Criar novas solicitações com base nos dados fornecidos.
          - 🔍 Consultar status, prazos, responsáveis ou comentários de solicitações já existentes.
          - ✏️ Atualizar qualquer campo ou progresso relacionado à solicitação.
          - 🗑️ Deletar solicitações quando explicitamente instruído.
        - UserProxyAgent → Gerencia a conversa e distribui tarefas entre os agentes com base nos pedidos do usuário.
        - graph_suggestion_agent → Gera visualizações e análises gráficas com base em dados **explicitamente fornecidos** pelo UserProxyAgent ou SheetsAgent.
        - AnalystAgent → Fornece insights, análises de negócio e sugestões de análises ou gráficos que podem ser realizados com base nos dados já extraídos. **Nunca executa a geração de gráficos ou relatórios sem autorização explícita do usuário.**

        Leia a conversa abaixo. Em seguida, selecione qual papel entre {participants} deve agir a seguir com base no contexto atual da tarefa e nas próximas ações esperadas.

        🚦 Regras de Roteamento:
        1. Só podem ser respondidas solicitações que estejam dentro do escopo das funções dos agentes definidos nesta estrutura. Ignorar ou recusar qualquer pedido que fuja ao escopo operacional dos agentes.
        2. Caso a mensagem contenha apenas cumprimentos ou perguntas genéricas como "oi", "tudo bem?", "olá", "bom dia", etc., o papel apropriado para responder é o UserProxyAgent, que deverá retornar uma mensagem amigável e listar suas funcionalidades.
        3. Caso a solicitação do usuário esteja fora do escopo das funções dos agentes, o UserProxyAgent deve responder educadamente que não poderá dar continuidade, listando as funções válidas.
        4. Se o usuário fez uma solicitação direta, o próximo papel é geralmente o UserProxyAgent.
        6. Se uma tarefa exige leitura ou extração de dados de planilhas, o papel adequado é o SheetsAgent.
        7. Se a tarefa exige análise visual ou criação de gráficos com dados já extraídos, o papel adequado é o graph_suggestion_agent.
        8. Se os dados vêm de e-mails, o GmailAgent deve atuar.
        9. Se a tarefa envolve qualquer operação de criação, consulta, atualização ou exclusão no quadro do Monday.com, acione o MondayAgent.
        10. Se a tarefa exigir análise crítica, geração de insights ou sugestões de análises de negócio/comportamento com base em dados já extraídos, acione o AnalystAgent (mas ele **não executa a geração de gráficos automaticamente**).
        11. Se mais de um papel precisa agir em sequência, retorne uma **lista ordenada** de papéis.
        12. Sempre considere o histórico da conversa para entender o fluxo completo.

        Histórico da conversa:
        {history}

        Com base no histórico acima, selecione o próximo papel entre {participants} que deve agir. Retorne apenas o nome do papel (ou lista de papéis).
        """

    selector_groupchat = SelectorGroupChat(
        agents,
        model_client=model_client,
        max_selector_attempts=3,
        selector_prompt=selector_prompt,
        termination_condition=TextMentionTermination(text="Aguardando sua confirmação")
    )

async def on_unhandled_message(message, ctx):
    if isinstance(message, GroupChatError):
        return {
            "conversation_id": str(uuid.uuid4()),
            "current_agent": "Sistema",
            "context": {
                "last_task": "Bloqueio por conteúdo",
                "cliente": "Não especificado"
            },
            "agents": [
                {"id": a["name"], "name": f"{a['avatar']} {a['name']}", "description": a["description"]}
                for a in AGENTS_META
            ],
            "events": [
                {"type": "agent_switch", "message": "Bloqueio de conteúdo", "agent": "Sistema", "timestamp": int(datetime.datetime.now().timestamp() * 1000)}
            ],
            "guardrails": [
                {
                    "id": "llama-guard",
                    "name": "llama-guard",
                    "input": message,
                    "reasoning": "Solicitação foi bloqueada por conter conteúdo inadequado.",
                    "passed": False,
                    "timestamp": datetime.datetime.now().isoformat()
                }
            ],
            "messages": [
                {"content": "❌ Sua solicitação foi bloqueada por violar as políticas de uso seguro do modelo de linguagem. Por favor, reformule o pedido de forma apropriada.", "agent": "Sistema"}
            ]
        }
    raise ValueError(f"Unhandled message in agent container: {type(message)}")

async def run_chat_async(msg, cancellation_token: asyncio.Event | None = None):
    try:
        # Aguarda até que o setup esteja completo, se necessário
        while selector_groupchat is None:
            await asyncio.sleep(0.1)

        message = msg  # Garante acesso à variável 'message' em todo o escopo

        normalized_msg = message.strip().lower()
        saudacoes = {"oi", "olá", "ola", "e aí", "bom dia", "boa tarde", "boa noite", "tudo bem?", "como vai?"}
        if normalized_msg in saudacoes:
            return {
                "conversation_id": str(uuid.uuid4()),
                "current_agent": "Sistema",
                "context": {
                    "last_task": "Saudação detectada",
                    "cliente": "Não especificado"
                },
                "agents": [
                    {"id": a["name"], "name": f"{a['avatar']} {a['name']}", "description": a["description"]}
                    for a in AGENTS_META
                ],
                "events": [
                    {"type": "agent_switch", "message": "Saudação recebida", "agent": "Sistema", "timestamp": int(datetime.datetime.now().timestamp() * 1000)}
                ],
                "guardrails": [
                    {
                        "id": "llama-guard",
                        "name": "llama-guard",
                        "input": message,
                        "reasoning": "Mensagem classificada como saudação genérica.",
                        "passed": True,
                        "timestamp": datetime.datetime.now().isoformat()
                    }
                ],
                "messages": [
                    {"content": "Olá! 😊 Sou um sistema inteligente que pode te ajudar com as seguintes tarefas:\n\n- 📧 Ler seus e-mails e extrair informações\n- 📊 Atualizar e registrar dados em planilhas\n- 📅 Atualizar o quadro de solicitações no Monday\n- 📈 Criar gráficos com dados fornecidos\n\nBasta me dizer o que você precisa!", "agent": "Sistema"}
                ]
            }

        task_result = None
        try:
            if cancellation_token and cancellation_token.is_set():
                print("🚫 Execução cancelada antes de iniciar.")
                return None
            async for result in selector_groupchat.run_stream(task=msg):
                if cancellation_token and cancellation_token.is_set():
                    print("🚫 Execução cancelada durante a execução do stream.")
                    return None

                task_result = result

        except Exception as e:
            print(f"Erro ao executar a tarefa: {e}")
            if "content_filter" in str(e):
                return {
                    "conversation_id": str(uuid.uuid4()),
                    "current_agent": "Sistema",
                    "context": {
                        "last_task": "Bloqueio por conteúdo",
                        "cliente": "Não especificado"
                    },
                    "agents": [
                        {"id": a["name"], "name": f"{a['avatar']} {a['name']}", "description": a["description"]}
                        for a in AGENTS_META
                    ],
                    "events": [
                        {"type": "agent_switch", "message": "Bloqueio de conteúdo", "agent": "Sistema", "timestamp": int(datetime.datetime.now().timestamp() * 1000)}
                    ],
                    "guardrails": [
                        {
                            "id": "llama-guard",
                            "name": "llama-guard",
                            "input": message,
                            "reasoning": "Solicitação foi bloqueada por conter conteúdo inadequado.",
                            "passed": False,
                            "timestamp": datetime.datetime.now().isoformat()
                        }
                    ],
                    "messages": [
                        {"content": "❌ Sua solicitação foi bloqueada por violar as políticas de uso seguro do modelo de linguagem. Por favor, reformule o pedido de forma apropriada.", "agent": "Sistema"}
                    ]
                }
            else:
                raise
        print("Resultado da tarefa:", task_result)
        if task_result and task_result.messages:
            last_message = next(
                (m for m in reversed(task_result.messages)
                 if getattr(m, "source", None) != "User"
                 and isinstance(m.content, str)
                 and m.content.strip()),
                None
            )

            if last_message:
                if "Tarefa não identificada" in getattr(task_result, "task", ""):
                    return {
                        "conversation_id": getattr(task_result, "thread", None) or str(uuid.uuid4()),
                        "current_agent": "Sistema",
                        "context": {
                            "last_task": getattr(task_result, "task", "Fora de escopo"),
                            "cliente": getattr(task_result, "cliente", "Não especificado")
                        },
                        "agents": [
                            {"id": a["name"], "name": f"{a['avatar']} {a['name']}", "description": a["description"]}
                            for a in AGENTS_META
                        ],
                        "events": [
                            {"type": "agent_switch", "message": "Solicitação fora do escopo", "agent": "Sistema", "timestamp": int(datetime.datetime.now().timestamp() * 1000)}
                        ],
                        "guardrails": [
                            {
                                "id": "llama-guard",
                                "name": "llama-guard",
                                "input": message,
                                "reasoning": "Solicitação fora do escopo das funcionalidades disponíveis.",
                                "passed": True,
                                "timestamp": datetime.datetime.now().isoformat()
                            }
                        ],
                        "messages": [
                            {"content": "Desculpe, essa solicitação está fora do meu escopo de atuação. Posso ajudar com:\n\n- 📧 Consultas a e-mails\n- 📊 Registros em planilhas\n- 📅 Atualizações no Monday.com\n- 📈 Geração de gráficos a partir de dados fornecidos\n\nPor favor, reformule seu pedido com uma dessas finalidades.", "agent": "Sistema"}
                        ]
                    }

                avatar = next((a["avatar"] for a in AGENTS_META if a["name"] == last_message.source), "💬")
                clean_content = last_message.content.replace("TERMINATE", "").strip()

                # Monta resposta com base nos dados reais
                response = {
                    "conversation_id": getattr(task_result, "thread", None) or str(uuid.uuid4()),
                    "current_agent": last_message.source,
                    "context": {
                        "last_task": getattr(task_result, "task", "Tarefa não identificada"),
                        "cliente": getattr(task_result, "cliente", "Não especificado")
                    },
                    "agents": [
                        {"id": a["name"], "name": f"{a['avatar']} {a['name']}", "description": a["description"]}
                        for a in AGENTS_META
                    ],
                    "events": [
                        {"type": "agent_switch", "message": f"Troca para {last_message.source}", "agent": last_message.source, "timestamp": int(last_message.created_at.timestamp() * 1000)}
                    ],
                    "guardrails": [
                        {
                            "id": "llama-guard",
                            "name": "llama-guard",
                            "input": message,
                            "reasoning": "Solicitação processada normalmente.",
                            "passed": True,
                            "timestamp": datetime.datetime.now().isoformat()
                        }
                    ],
                    "messages": [
                        {"content": clean_content, "agent": last_message.source}
                    ]
                }
                print(response)
                return response

    except Exception as e:
        print(e)
        return {"sender": "Sistema", "avatar": "⚠️", "content": f"Erro: {e}"}

    return None



# --- FastAPI WebSocket Server (escopo global) ---
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app):
    await setup_agents()
    yield

app_ws = FastAPI(lifespan=lifespan)

@app_ws.websocket("/ws/chat")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_json()
            print("data: ", data)
            message = data.get("message", "")

            if not is_safe_input(message):
                await websocket.send_json({
                    "conversation_id": str(uuid.uuid4()),
                    "current_agent": "Sistema",
                    "context": {
                        "last_task": "Bloqueio por conteúdo",
                        "cliente": "Não especificado"
                    },
                    "agents": [
                        {"id": a["name"], "name": f"{a['avatar']} {a['name']}", "description": a["description"]}
                        for a in AGENTS_META
                    ],
                    "events": [
                        {"type": "agent_switch", "message": "Bloqueio de conteúdo", "agent": "Sistema", "timestamp": int(datetime.datetime.now().timestamp() * 1000)}
                    ],
                    "guardrails": [
                        {
                            "id": "llama-guard",
                            "name": "llama-guard",
                            "input": message,
                            "reasoning": "Conteúdo bloqueado por violar as políticas de segurança.",
                            "passed": False,
                            "timestamp": datetime.datetime.now().isoformat()
                        }
                    ],
                    "messages": [
                        {"content": "❌ Sua solicitação foi bloqueada por violar as políticas de uso seguro do modelo de linguagem. Por favor, reformule o pedido de forma apropriada.", "agent": "Sistema"}
                    ]
                })
                continue

            try:
                result = await run_chat_async(message, cancellation_token=shutdown_event)
                await websocket.send_json(result)
            except Exception as e:
                await websocket.send_json({
                    "thread_id": None,
                    "message": "Ocorreu um erro durante o processamento da solicitação.",
                    "guardrails": [{
                        "id": "llama-guard",
                        "name": "llama-guard",
                        "input": message,
                        "reasoning": str(e),
                        "passed": False,
                        "timestamp": datetime.datetime.now().isoformat()
                    }]
                })

    except WebSocketDisconnect:
        print("🔌 WebSocket desconectado.")

import signal

shutdown_event = asyncio.Event()

def shutdown():
    print("🔴 Interrupção detectada. Encerrando com segurança...")
    shutdown_event.set()

signal.signal(signal.SIGINT, lambda sig, frame: shutdown())
signal.signal(signal.SIGTERM, lambda sig, frame: shutdown())

if __name__ == "__main__":
    import uvicorn

    async def run():
        config = uvicorn.Config("main:app_ws", host="0.0.0.0", port=8000, reload=True)
        server = uvicorn.Server(config)
        await server.serve()

    async def main():
        server_task = asyncio.create_task(run())
        await shutdown_event.wait()
        server_task.cancel()
        try:
            await server_task
        except asyncio.CancelledError:
            print("✅ Servidor encerrado.")

    asyncio.run(main())