import asyncio
from agent.sheets.agent import build_agent


async def main():
    # Cria o agente
    agent = await build_agent()

    try:
        result = await agent.run(task="Registrar nova solicitação com prioridade Alta para venda de equipamentos industriais feita por João Silva no dia 21/06/2025. Valor de R$25.000,00 para o cliente ACME. Departamento: Compras. Status: Pendente.")
        print(result.messages)
    except Exception as e:
        print("Erro durante a execução do agente:", str(e))

if __name__ == "__main__":
    asyncio.run(main())