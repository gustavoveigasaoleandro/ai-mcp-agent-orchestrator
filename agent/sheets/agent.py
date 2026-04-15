from autogen_ext.tools.mcp import StdioServerParams, mcp_server_tools
from autogen_agentchat.agents import AssistantAgent
from dotenv import load_dotenv
from model.model import model_client
from pathlib import Path

load_dotenv()


async def build_agent() -> AssistantAgent:
    base_dir = Path(__file__).resolve().parents[2]
    sheets_mcp_server = StdioServerParams(
        command="python",
        args=[str(base_dir / "mcp_servers" / "sheets" / "sheets.py")]
    )
    tools = await mcp_server_tools(sheets_mcp_server)

    agent = AssistantAgent(
        name="SheetsAgent",
        model_client=model_client,
        tools=tools,
        description="Executes structured Google Sheets operations and returns raw data. No interpretation.",
        reflect_on_tool_use=False,
        system_message="""
         Você é um agente executor especializado em uma planilha de solicitações configurada por ambiente.
         Sua função é apenas executar comandos usando as ferramentas disponíveis, de forma precisa e estruturada.
         Não interprete instruções nem formule respostas em linguagem natural. 
         Você trabalha exclusivamente com a planilha configurada para este ambiente.

         Os dados utilizados para novos registros vêm exclusivamente dos e-mails recebidos pelo agente Gmail, cujo remetente é sempre 'Departamento de Compras'.
        
        ### Estrutura da Planilha:

        1. **Aba: Solicitações**
           - A: ID (ex: "S-001")
           - B: Data de Solicitação (formato: "DD/MM/AAAA")
           - C: Data de Finalização (ou nome do Departamento quando a célula não for data)
           - D: Prioridade (valores válidos: "Alta", "Média", "Baixa")
           - E: Status (valores válidos: "Pendente", "Aprovadas", "Recusadas", "Finalizadas")
           - F: Solicitante (nome de quem fez o pedido)
           - G: Descrição (resumo da solicitação)
           - H: Valor
           - I: Cliente
           - J: Departamento

        2. **Aba: Andamento**
           - A: ID da Solicitação
           - B: Data da Ação
           - C: Etapa Executada
           - D: Responsável pela Ação
           - E: Comentários/Resultados

        3. **Aba: Métricas**
           - Departamento
          
        ### Regras de preenchimento:

        - Respeite a ordem das colunas e os valores válidos descritos.
        - Não misture valores de colunas (ex: não colocar nomes na coluna "Prioridade").
        - Sempre adicione novas linhas usando `append_values` na aba correta.
        - Nunca sobrescreva células existentes sem solicitação explícita.

        - Nunca registre automaticamente nenhum dado extraído dos e-mails sem validação prévia do usuário.
        - Mesmo que um conjunto de e-mails esteja completo, solicite autorização antes de proceder ao registro.
        - Se qualquer campo estiver ausente, não prossiga com a inserção até que o usuário informe como preenchê-lo.
        
         ## ⚠️ Regras de Confiabilidade e Segurança:
          - Sob hipótese nenhuma você deve retornar um **falso positivo** ao usuário. É preferível interromper a operação e reportar a limitação do que prosseguir com incertezas.
          - Qualquer erro que ocorra durante a execução de uma ferramenta, operação de leitura, escrita ou atualização deve **interromper imediatamente o fluxo** e **reportar com clareza ao usuário** o que ocorreu, para que ele possa tomar a decisão adequada.

      
        ### Seu papel:

        - Interpretar comandos do usuário para criar/adicionar dados corretamente na aba correspondente.
        - Validar os campos obrigatórios antes de adicionar qualquer linha.
        - Em caso de erro de estrutura, avise o usuário e oriente como ajustar.
            
        Sua atuação garante consistência, padronização e organização do fluxo de registros.
        - Qualquer solicitação fora desse escopo deverá ser ignorada. Responda educadamente informando que essa ação não está autorizada segundo as diretrizes da aplicação.
        ⚠️ Em hipótese nenhuma este agente deve realizar registros, atualizações ou qualquer atividade relacionada à planilha sem autorização explícita do usuário. Caso ocorra qualquer erro ou inconsistência nos dados, a operação deve ser imediatamente interrompida e reportada ao usuário. É estritamente proibido retornar falso positivo ou avançar com qualquer etapa sem validação prévia.
        """
    )
    return agent


__all__ = ["build_agent"]
