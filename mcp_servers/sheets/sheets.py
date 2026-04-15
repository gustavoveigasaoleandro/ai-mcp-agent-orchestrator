import re
from typing import List
from googleapiclient.errors import HttpError
from mcp.server.fastmcp import FastMCP

from helpers import authenticate_sheets

# Estrutura fixa da planilha usada no caso de uso
PLANILHA_NOME = "Registro de Solicitações - 2024"
ABA_SOLICITACOES = "Solicitações!A2:J"
ABA_ANDAMENTO = "Andamento!A2:E"
ABA_METRICAS = "Métricas!A2:E"

# Initialize FastMCP server
mcp = FastMCP("sheets")

USER_AGENT = "sheets-app/1.0"

from googleapiclient.discovery import build

# Autenticação (reaproveita lógica do Gmail se estiver em helpers)
from helpers import authenticate_sheets

@mcp.tool("create_spreadsheet", description="Cria uma nova planilha no Google Sheets com um nome especificado.")
def create_spreadsheet(title: str) -> dict:
    service = authenticate_sheets()
    spreadsheet = {
        'properties': {'title': title}
    }
    result = service.spreadsheets().create(body=spreadsheet).execute()
    return result

@mcp.tool("get_spreadsheet_info", description="Retorna informações completas sobre uma planilha com base no ID.")
def get_spreadsheet_info(spreadsheet_id: str) -> dict:
    service = authenticate_sheets()
    result = service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
    return result

@mcp.tool("get_range_values", description="Retorna os valores de um intervalo da planilha.")
def get_range_values(spreadsheet_id: str, range_str: str) -> dict:
    service = authenticate_sheets()
    result = service.spreadsheets().values().get(spreadsheetId=spreadsheet_id, range=range_str).execute()
    return result

@mcp.tool("append_values", description="Adiciona valores ao final de um intervalo existente na planilha com verificação.")
def append_values(spreadsheet_id: str, range_str: str, values: List[List[str]]) -> dict:
    service = authenticate_sheets()
    # Verificar se a solicitação já existe
    existing_data = service.spreadsheets().values().get(
        spreadsheetId=spreadsheet_id,
        range="Solicitações!A2:F"
    ).execute().get("values", [])

    for row in existing_data:
        if len(row) >= 6 and row[1] == values[0][1] and row[3] == values[0][3] and row[5] == values[0][5]:
            raise ValueError("Solicitação já existente com mesma Data, Solicitante e Descrição.")

    body = {"values": values}
    result = service.spreadsheets().values().append(
        spreadsheetId=spreadsheet_id,
        range=range_str,
        valueInputOption="USER_ENTERED",
        body=body
    ).execute()
    return result

@mcp.tool("update_range_values", description="Atualiza valores em um intervalo específico da planilha.")
def update_range_values(spreadsheet_id: str, range_str: str, values: List[List[str]]) -> dict:
    service = authenticate_sheets()
    body = {"values": values}
    result = service.spreadsheets().values().update(
        spreadsheetId=spreadsheet_id,
        range=range_str,
        valueInputOption="USER_ENTERED",
        body=body
    ).execute()
    return result


@mcp.tool("batch_update_values", description="Atualiza múltiplos intervalos de uma planilha.")
def batch_update_values(spreadsheet_id: str, data: List[dict]) -> dict:
    service = authenticate_sheets()
    body = {
        "valueInputOption": "USER_ENTERED",
        "data": data
    }
    result = service.spreadsheets().values().batchUpdate(
        spreadsheetId=spreadsheet_id,
        body=body
    ).execute()
    return result

# Novas ferramentas conforme solicitado:

@mcp.tool("batch_get_values", description="Retorna múltiplos intervalos de valores de uma planilha.")
def batch_get_values(spreadsheet_id: str, ranges: List[str]) -> dict:
    service = authenticate_sheets()
    result = service.spreadsheets().values().batchGet(
        spreadsheetId=spreadsheet_id,
        ranges=ranges
    ).execute()
    return result

@mcp.tool("batch_update_by_data_filter", description="Atualiza múltiplos intervalos com base em filtros de dados.")
def batch_update_by_data_filter(spreadsheet_id: str, data: List[dict]) -> dict:
    service = authenticate_sheets()
    body = {
        "valueInputOption": "USER_ENTERED",
        "data": data
    }
    result = service.spreadsheets().values().batchUpdateByDataFilter(
        spreadsheetId=spreadsheet_id,
        body=body
    ).execute()
    return result

@mcp.tool("get_developer_metadata", description="Retorna os metadados do desenvolvedor de uma planilha.")
def get_developer_metadata(spreadsheet_id: str, metadata_id: int) -> dict:
    service = authenticate_sheets()
    result = service.spreadsheets().developerMetadata().get(
        spreadsheetId=spreadsheet_id,
        metadataId=metadata_id
    ).execute()
    return result

@mcp.tool("search_developer_metadata", description="Busca metadados do desenvolvedor com base em filtros.")
def search_developer_metadata(spreadsheet_id: str, data_filter: dict) -> dict:
    service = authenticate_sheets()
    body = {"dataFilter": data_filter}
    result = service.spreadsheets().developerMetadata().search(
        spreadsheetId=spreadsheet_id,
        body=body
    ).execute()
    return result

@mcp.tool("clear_range", description="Limpa os valores de um intervalo da planilha.")
def clear_range(spreadsheet_id: str, range_str: str) -> dict:
    service = authenticate_sheets()
    result = service.spreadsheets().values().clear(
        spreadsheetId=spreadsheet_id,
        range=range_str,
        body={}
    ).execute()
    return result

@mcp.tool("batch_clear_ranges", description="Limpa múltiplos intervalos da planilha.")
def batch_clear_ranges(spreadsheet_id: str, ranges: List[str]) -> dict:
    service = authenticate_sheets()
    body = {"ranges": ranges}
    result = service.spreadsheets().values().batchClear(
        spreadsheetId=spreadsheet_id,
        body=body
    ).execute()
    return result

@mcp.tool("copy_sheet_to_another", description="Copia uma aba de uma planilha para outra planilha de destino.")
def copy_sheet_to_another(spreadsheet_id: str, sheet_id: int, destination_spreadsheet_id: str) -> dict:
    service = authenticate_sheets()
    request_body = {"destinationSpreadsheetId": destination_spreadsheet_id}
    result = service.spreadsheets().sheets().copyTo(
        spreadsheetId=spreadsheet_id,
        sheetId=sheet_id,
        body=request_body
    ).execute()
    return result

@mcp.tool("add_request", description="Add a new row to the 'Solicitações' sheet tab.")
def add_request(spreadsheet_id: str, dados: dict) -> dict:
    valores = [[
        dados.get("id"), dados.get("data"), dados.get("departamento"),
        dados.get("solicitante"), dados.get("tipo"),
        dados.get("descricao"), dados.get("prioridade"),
        dados.get("status"), dados.get("responsavel"),
        dados.get("link_monday")
    ]]
    return append_values(spreadsheet_id, ABA_SOLICITACOES, valores)

@mcp.tool("register_progress_step", description="Register a new progress step for the request.")
def register_progress_step(spreadsheet_id: str, dados: dict) -> dict:
    valores = [[
        dados.get("id"), dados.get("data_acao"), dados.get("etapa_executada"),
        dados.get("responsavel"), dados.get("comentario")
    ]]
    return append_values(spreadsheet_id, ABA_ANDAMENTO, valores)

@mcp.tool("list_requests", description="Return all registered requests.")
def list_requests(spreadsheet_id: str) -> dict:
    return get_range_values(spreadsheet_id, ABA_SOLICITACOES)

@mcp.tool("clear_requests_tab", description="Clear all data from the 'Solicitações' sheet tab (excluding headers).")
def clear_requests_tab(spreadsheet_id: str) -> dict:
    return clear_range(spreadsheet_id, ABA_SOLICITACOES)

@mcp.tool("get_department_metrics", description="Fetch department metrics data from the 'Métricas' sheet tab.")
def get_department_metrics(spreadsheet_id: str) -> dict:
    return get_range_values(spreadsheet_id, ABA_METRICAS)


# Gera um identificador único aleatório para novas solicitações.
import uuid

@mcp.tool("generate_unique_id", description="Generate a unique identifier for a new request.")
def gerar_id_unico() -> dict:
    return {"id": str(uuid.uuid4())}

if __name__ == "__main__":
    mcp.run(transport="stdio")