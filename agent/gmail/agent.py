from autogen_ext.tools.mcp import StdioServerParams, mcp_server_tools
from autogen_agentchat.agents import AssistantAgent
from dotenv import load_dotenv
from model.model import model_client
from pathlib import Path

load_dotenv()

async def build_agent() -> AssistantAgent:
    base_dir = Path(__file__).resolve().parents[2]
    gmail_mcp_server = StdioServerParams(
        command="python",
        args=[str(base_dir / "mcp_servers" / "gmail" / "gmail.py")]
    )
    tools = await mcp_server_tools(gmail_mcp_server)
    agent = AssistantAgent(
        name="GmailAgent",
        description=(
            "Agente dedicado à extração de dados de e-mails do remetente “Departamento de compras”, com foco exclusivo em interpretação e estruturação das informações, sem realizar qualquer ação de registro ou alteração sem a autorização explícita do usuário."
        ),
        model_client=model_client,
        tools=tools,
        reflect_on_tool_use=True,
        system_message=(
            "Este agente será utilizado exclusivamente para processar mensagens enviadas por um remetente chamado \"Departamento de compras\", relacionadas a solicitações de compra. Sua função é extrair dados estruturados desses e-mails conforme os seguintes campos obrigatórios da planilha:\n"
            "\n"
            "1. ID  \n"
            "2. Data de Solicitação  \n"
            "3. Data de Finalização  \n"
            "4. Prioridade  \n"
            "5. Status  \n"
            "6. Solicitante  \n"
            "7. Descrição  \n"
            "8. Valor  \n"
            "9. Cliente  \n"
            "10. Departamento\n"
            "\n"
            "⚠️ Regras:\n"
            "- Os dados devem ser extraídos exclusivamente do conteúdo do e-mail.\n"
            "- Sob hipótese nenhuma deve-se registrar dados automaticamente na planilha, mesmo que apenas parcialmente preenchidos.\n"
            "- Caso algum campo esteja ausente, o agente deverá solicitar orientação do usuário antes de prosseguir.\n"
            "- Nunca utilizar valores padrão, inferências ou campos em branco.\n"
            "- Sempre retornar ao usuário um resumo com todos os campos no formato da planilha, destacando eventuais ausências e solicitando confirmação explícita para registro.\n"
            "- Sob hipótese nenhuma deve ser retornado um falso positivo ao usuário. Em caso de erro na extração ou inconsistência de dados, a operação deve ser imediatamente interrompida e o erro reportado.\n"
            "- Em hipótese alguma deve ser realizado qualquer processo de registro, atualização ou modificação de dados, seja na planilha ou em outros sistemas, sem a autorização explícita e confirmada do usuário.\n"
        )
    )
    return agent

__all__ = ["build_agent"]
