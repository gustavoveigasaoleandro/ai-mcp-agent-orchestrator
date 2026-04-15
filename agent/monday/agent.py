from autogen_ext.tools.mcp import StdioServerParams, mcp_server_tools
from autogen_agentchat.agents import AssistantAgent
from azure.core.credentials import AzureKeyCredential
from autogen_ext.models.azure import AzureAIChatCompletionClient
from dotenv import load_dotenv
from model.model import model_client
import os
load_dotenv()
async def build_agent() -> AssistantAgent:
    # Setup server params for local filesystem access
    monday_mcp_server = StdioServerParams(
        command="npx",
        args=[
            "@mondaydotcomorg/monday-api-mcp",
            "-t",
            os.getenv("MONDAY_TOKEN"),
            "--enable-dynamic-api-tools",
            "true"
          ]
    )

    tools = await mcp_server_tools(monday_mcp_server)

    agent = AssistantAgent(
        name="MondayAgent",
        description=f"Você é um assistente de IA especializado em auxiliar usuários no gerenciamento de projetos e fluxos de trabalho dentro da plataforma Monday.com, utilizando as ferramentas da API de forma eficiente, segura e automatizada. Você está operando no quadro '{os.getenv('MONDAY_BOARD_NAME')}' (ID: {os.getenv('MONDAY_BOARD_ID')}).",
        model_client=model_client,
        tools=tools,
        reflect_on_tool_use=True,
        system_message=f"""
        Você é um agente executor especializado na integração com a plataforma Monday.com, usando as ferramentas expostas pelo MCP server customizado da organização.

        - Sob hipótese nenhuma este agente deve realizar registros, atualizações ou qualquer tipo de alteração nos dados do Monday sem a autorização explícita do usuário.
        - Em caso de erro ou inconsistência na extração ou interpretação dos dados, o processo deve ser imediatamente interrompido e o usuário informado sem qualquer tentativa de correção automática ou inferência.

        Seu papel é executar operações de **CRUD (Criar, Ler, Atualizar, Deletar)** de forma estruturada, eficiente e segura. Você **não é um agente restrito a registros** — pode também ler dados, buscar itens por grupo, alterar colunas, mover entre grupos, excluir, arquivar e mais.

        ## 🧩 Estrutura da Integração:
        - Você atua exclusivamente sobre o board "{os.getenv("MONDAY_BOARD_NAME")}" cujo **ID fixo e obrigatório é `{os.getenv("MONDAY_BOARD_ID")}`**.
        - Os registros estão organizados em grupos com status: **Pendentes, Aprovadas, Recusadas, Finalizadas**.
        - Cada item possui colunas como: ID, Item, Departamento, Data, Solicitante, Prioridade, entre outras.

        ## 🔎 Consulta de Dados (all_monday_api):
        Para consultar todos os registros do board, utilize sempre a função `all_monday_api`


        ## ⚠️ Regras de Confiabilidade e Segurança:
        - Sob hipótese nenhuma você deve retornar um **falso positivo** ao usuário. É preferível interromper a operação e reportar a limitação do que prosseguir com incertezas.
        - Qualquer erro que ocorra durante a execução de uma ferramenta, operação de leitura, escrita ou atualização deve **interromper imediatamente o fluxo** e **reportar com clareza ao usuário** o que ocorreu, para que ele possa tomar a decisão adequada.
        """
    )
    return agent


__all__ = ["build_agent"]