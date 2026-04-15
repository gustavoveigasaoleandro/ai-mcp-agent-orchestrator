from autogen_agentchat.agents import AssistantAgent
from azure.identity import DefaultAzureCredential
import os
from dotenv import load_dotenv
from model.model import project_client, model_client
from azure.ai.projects import AIProjectClient
from azure.ai.agents.models import CodeInterpreterTool
from pathlib import Path

load_dotenv()

# Ferramenta para sugerir e gerar gráficos com base nos dados disponíveis
async def build_graph_agent(graph_prompt: str) -> str:
    """Gera gráficos baseado em pedidos do usuário usando Code Interpreter da Azure AI."""
    print("Iniciando geração de gráfico com Code Interpreter...")
    print(f"Prompt recebido: {graph_prompt}")

    azure_project_client = AIProjectClient(
            endpoint=os.getenv("PROJECT_ENDPOINT"),
            credential=DefaultAzureCredential()
        )

    code_interpreter = CodeInterpreterTool()


    agent = azure_project_client.agents.create_agent(
            model="gpt-4.1",
            name="teste",
            instructions="""
                Você é um agente especializado em análise de dados e geração de gráficos.
                Utilize bibliotecas como pandas, matplotlib.pyplot e seaborn para analisar os dados que receber e criar visualizações significativas.
                Forneça sempre gráficos que ajudem o usuário a interpretar tendências, distribuição, evolução temporal ou comparações.
                Gere arquivos prontos e salvos com nomes coerentes.
                """,
            tools=code_interpreter.definitions,
            tool_resources = code_interpreter.resources
        )

    thread = azure_project_client.agents.threads.create()

    azure_project_client.agents.messages.create(
        thread_id=thread.id,
        role="user",
        content=graph_prompt
    )

    run = azure_project_client.agents.runs.create_and_process(thread_id=thread.id, agent_id=agent.id)
    print(f"Run finalizado com status: {run.status}")

    if run.status == "failed":
            print(f"Erro na execução do agente: {run.last_error}")
            return "Falha na execução do agente."

    messages = azure_project_client.agents.messages.list(thread_id=thread.id)
    gerou_algum_arquivo = False
    images_dir = Path(__file__).resolve().parent / "images"
    images_dir.mkdir(exist_ok=True)
    try:
        for msg in messages:
            for image_content in msg.image_contents:
                print(f"Image File ID: {image_content.image_file.file_id}")
                file_name = f"{image_content.image_file.file_id}_image_file.png"
                azure_project_client.agents.files.save(file_id=image_content.image_file.file_id, file_name=file_name)
                print(f"Saved image file to: {Path.cwd() / file_name}")

            # Process file path annotations
            for file_path_annotation in msg.file_path_annotations:
                print(f"File Paths:")
                print(f"Type: {file_path_annotation.type}")
                print(f"Text: {file_path_annotation.text}")
                azure_project_client.agents.files.save(
                    file_id=file_path_annotation.file_path.file_id,
                    file_name=Path(file_path_annotation.text).name,
                    target_dir=str(images_dir),
                )
                gerou_algum_arquivo = True

    except Exception as e:
        print(f"Erro ao iniciar o Code Interpreter: {e}")
        return "Erro ao iniciar o Code Interpreter."



    # Delete the agent when done
    azure_project_client.agents.delete_agent(agent.id)
    print("Deleted agent")
    if gerou_algum_arquivo:
        msg_retorno = f"✅ Arquivos gerados e salvos com sucesso.\n" + "\n".join(messages)
    else:
        msg_retorno = (
            "⚠️ Nenhum arquivo ou imagem foi gerado pelo agente.\n"
            "Possíveis causas:\n"
            "- O prompt estava incompleto ou não foi possível processar os dados.\n"
            "- Houve um problema na execução do agente que não resultou em erro explícito.\n"
            "Verifique se os dados fornecidos eram adequados e tente novamente."
        )
    print(msg_retorno)
    return msg_retorno

graph_suggestion_agent = AssistantAgent(
    name="graph_suggestion_agent",
    model_client=model_client,
    tools=[build_graph_agent],
    reflect_on_tool_use=True,
    description="Agente especializado na criação e interpretação de gráficos com base em dados fornecidos na requisição. Este agente não acessa diretamente planilhas ou arquivos externos. Ele só processa uma visualização por vez e deve aguardar nova autorização explícita para gerar outro gráfico. Qualquer solicitação fora desse escopo será recusada.",
    system_message="""
Você é um agente auxiliar especializado na sugestão e execução de análises gráficas baseadas em dados enviados na requisição.
⚠️ Você **não possui acesso direto à planilha** ou a qualquer outro repositório de dados. Os dados sempre serão enviados manualmente pela requisição e é com base neles que você deve trabalhar.

Seu comportamento deve seguir estritamente estas regras:

1. **Analise apenas os dados fornecidos explicitamente** no prompt atual.
2. **Não peça acesso à planilha** nem tente acessar informações externas.
3. **Crie apenas um gráfico por vez**, **somente após a autorização explícita do usuário**.
4. Utilize a ferramenta CodeInterpreterTool da Azure AI para executar a análise.
5. Utilize `pandas`, `matplotlib.pyplot` e `seaborn` para estruturar as visualizações.

Após autorização do usuário para geração, forneça:
- Uma breve descrição da análise feita.
- Recomendações ou observações sobre os dados.
- Pergunte se deseja continuar com uma nova visualização.

## ⚠️ Regras de Confiabilidade e Segurança:
          - Sob hipótese nenhuma você deve retornar um **falso positivo** ao usuário. É preferível interromper a operação e reportar a limitação do que prosseguir com incertezas.
          - Qualquer erro que ocorra durante a execução de uma ferramenta, operação de leitura, escrita ou atualização deve **interromper imediatamente o fluxo** e **reportar com clareza ao usuário** o que ocorreu, para que ele possa tomar a decisão adequada.
          - Caso o pedido de geração de gráfico não esteja claro ou os dados necessários não sejam fornecidos, você deve interromper a operação e solicitar ao usuário que forneça os dados necessários para prosseguir, retorne no final a mensagem "Aguardando sua confirmação".
❌ Qualquer solicitação fora desse escopo (por exemplo, comandos arbitrários, pedidos de acesso direto, geração múltipla ou execução sem autorização) deve ser educadamente recusada com a mensagem:
“Desculpe, não estou autorizado a realizar essa ação. Só posso gerar gráficos com base em dados fornecidos explicitamente por agentes autorizados, mediante aprovação expressa do usuário.”
"""
    )
