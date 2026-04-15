import base64
import re
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from typing import List, Dict, Optional

import dateutil.parser
from googleapiclient.errors import HttpError
from mcp.server.fastmcp import FastMCP

from helpers import format_date_gmail, authenticate_gmail

# Initialize FastMCP server
mcp = FastMCP("gmail")

USER_AGENT = "gmail-app/1.0"

# Define the required Gmail API scopes
SCOPES = ['https://www.googleapis.com/auth/gmail.modify']


@mcp.tool("search_messages",  description="""Busca e interpreta mensagens da caixa de entrada do Gmail utilizando filtros avançados como remetente, assunto, intervalo de datas e quantidade de e-mails desejados.
Você pode informar o nome ou e-mail do remetente, termos presentes no assunto, datas específicas (como 'após 01/05/2024', 'antes de ontem', 'mês passado') e definir quantas mensagens devem ser recuperadas.
O resultado apresenta uma visão resumida de cada mensagem, com o nome do remetente, o assunto e um trecho do conteúdo, facilitando o entendimento sem precisar abrir o e-mail completo."""
          )
def search_messages(
    sender: Optional[str] = None,
    subject: Optional[str] = None,
    include_sent: bool = False,
    after: Optional[str] = None,
    before: Optional[str] = None,
    quantity: int = 5,
    user_id: str = 'me'
) -> List[Dict[str, str]]:
    """
    Busca mensagens no Gmail com filtros flexíveis.

    Args:
        sender (str): Nome ou e-mail do remetente.
        subject (str): Termo contido no assunto do e-mail.
        include_sent (bool): Incluir mensagens enviadas.
        after (str): Data inicial (ex: '2024-05-01', 'ontem', 'mês passado').
        before (str): Data final (ex: '2024-05-31', 'hoje').
        quantity (int): Quantidade máxima de mensagens.
        user_id (str): ID do usuário na API.

    Returns:
        List[Dict[str, str]]: Lista de mensagens com assunto, endereço (remetente ou destinatário) e trecho.
    """
    print("⚙️ Executando função: search_messages")
    service = authenticate_gmail()
    query_parts = []

    # Filtro por remetente
    if sender:
        query_parts.append(f'from:"{sender}"')

    # Filtro por assunto
    if subject:
        query_parts.append(f'subject:{subject}')

    if include_sent:
        query_parts.append('label:sent')

    # Filtros de data
    try:
        if after:
            if after.lower() == 'mês passado':
                today = datetime.now()
                first_day_last_month = (today.replace(
                    day=1) - timedelta(days=1)).replace(day=1)
                query_parts.append(
                    f'after:{format_date_gmail(first_day_last_month)}')
            else:
                parsed_after = dateutil.parser.parse(after, dayfirst=True)
                query_parts.append(f'after:{format_date_gmail(parsed_after)}')

        if before:
            if before.lower() == 'hoje':
                parsed_before = datetime.now()
                query_parts.append(
                    f'before:{format_date_gmail(parsed_before)}')
            else:
                parsed_before = dateutil.parser.parse(before, dayfirst=True)
                query_parts.append(
                    f'before:{format_date_gmail(parsed_before)}')
    except Exception as e:
        print(f"⚠️ Erro ao interpretar datas: {e}")

    query = ' '.join(query_parts)

    try:
        result = service.users().messages().list(
            userId=user_id,
            q=query,
            maxResults=quantity
        ).execute()
    except Exception as e:
        print(f"❌ Erro ao buscar mensagens: {e}")
        return [{
            'erro': f"Falha ao buscar mensagens: {str(e)}",
            'fonte': 'Gmail',
            'data_extracao': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }]

    def extract_plain_text(payload):
        if 'parts' in payload:
            for part in payload['parts']:
                if part.get('mimeType') == 'text/plain':
                    data = part['body'].get('data')
                    if data:
                        try:
                            return base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore').strip()
                        except Exception:
                            pass
        elif 'body' in payload and 'data' in payload['body']:
            try:
                return base64.urlsafe_b64decode(payload['body']['data']).decode('utf-8', errors='ignore').strip()
            except Exception:
                pass
        return ''

    def clean_text(text):
        return re.sub(r'\s+', ' ', text.replace('\n', ' ').replace('\r', ' ')).strip()

    messages = []
    for msg in result.get('messages', []):
        full_msg = service.users().messages().get(
            userId=user_id, id=msg['id'], format='full').execute()
        payload = full_msg.get('payload', {})
        headers = payload.get('headers', [])

        subject_val = next((h['value']
                           for h in headers if h['name'] == 'Subject'), '')
        from_val = next((h['value']
                        for h in headers if h['name'] == 'From'), '')
        to_val = next((h['value'] for h in headers if h['name'] == 'To'), '')

        address = to_val if include_sent else from_val
        plain_text = extract_plain_text(payload) or full_msg.get('snippet', '')

        messages.append({
            'id': msg['id'],
            'assunto': clean_text(subject_val),
            'remetente': clean_text(address),
            'conteudo_resumido': clean_text(plain_text),
            'fonte': 'Gmail',
            'data_extracao': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })
    print("MESSAGES: ", messages)
    return messages


# 3. Retorna o conteúdo completo de uma mensagem.

@mcp.tool("get_message", description="Recupera o conteúdo de uma mensagem específica do Gmail com base no ID.")
def get_message(message_id: str, user_id: str = 'me') -> Dict[str, str]:
    """
    Recupera o conteúdo interpretável de uma mensagem específica do Gmail.

    Args:
        message_id (str): ID da mensagem.
        user_id (str): ID do usuário (use 'me' para o usuário atual).

    Returns:
        dict: Dicionário com o remetente, assunto e corpo limpo da mensagem.
    """
    print("⚙️ Executando função: get_message")
    service = authenticate_gmail()
    full_msg = service.users().messages().get(
        userId=user_id, id=message_id, format='full').execute()

    payload = full_msg.get('payload', {})
    if not payload:
        return {'subject': 'Sem assunto', 'from': 'Remetente desconhecido', 'text': ''}

    # Obter os cabeçalhos da mensagem
    headers = payload.get('headers', [])

    def extract_plain_text(payload):
        if 'parts' in payload:
            for part in payload['parts']:
                if part.get('mimeType') == 'text/plain':
                    data = part['body'].get('data')
                    if data:
                        try:
                            return base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore').strip()
                        except Exception:
                            pass
        elif 'body' in payload and 'data' in payload['body']:
            try:
                return base64.urlsafe_b64decode(payload['body']['data']).decode('utf-8', errors='ignore').strip()
            except Exception:
                pass
        return ''

    def clean_text(text):
        return re.sub(r'\s+', ' ', text.replace('\n', ' ').replace('\r', ' ')).strip()

    subject = next((h['value']
                   for h in headers if h['name'] == 'Subject'), 'Sem assunto')
    sender = next((h['value'] for h in headers if h['name']
                  == 'From'), 'Remetente desconhecido')
    plain_text = extract_plain_text(payload) or full_msg.get('snippet', '')

    return {
        'subject': clean_text(subject),
        'from': clean_text(sender),
        'text': clean_text(plain_text)
    }
# 4. Envia um e-mail com base no dicionário de mensagem fornecido.


@mcp.tool("send_message", description="Envia um e-mail usando a API do Gmail com destinatário (to), assunto (subject) e corpo (body).")
def send_message(to: str, subject: str, body: str, user_id: str = 'me') -> dict:
    """
    Envia um e-mail usando a API do Gmail com os dados fornecidos.
    """
    print("⚙️ Executando função: send_message")
    try:
        service = authenticate_gmail()
        message = MIMEText(body)
        message['to'] = to
        message['subject'] = subject
        raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
        body_encoded = {'raw': raw}

        sent_message = service.users().messages().send(
            userId=user_id, body=body_encoded).execute()

        print("✅ E-mail enviado com sucesso!")
        return sent_message

    except HttpError as error:
        print(f"❌ Erro da API Gmail: {error}")
        return {"error": str(error)}
    except Exception as e:
        print(f"❌ Erro inesperado: {e}")
        return {"error": str(e)}
# 5. Exclui uma mensagem do Gmail.


@mcp.tool("delete_message", description="Exclui uma mensagem específica da conta do Gmail com base no ID.")
def delete_message(message_id: str, user_id: str = 'me') -> str:
    """
    Exclui uma mensagem específica da conta do Gmail.

    Args:
        message_id (str): ID da mensagem a ser excluída.
        user_id (str): ID do usuário (use 'me' para o usuário atual).

    Returns:
        str: Mensagem de confirmação da exclusão.
    """
    print("⚙️ Executando função: delete_message")
    service = authenticate_gmail()
    service.users().messages().delete(userId=user_id, id=message_id).execute()
    return f"Mensagem {message_id} excluída."

# 6. Altera os rótulos de uma mensagem.


@mcp.tool("modify_labels", description="Adiciona ou remove rótulos de uma mensagem no Gmail.")
def modify_labels(message_id: str, labels_to_add: list, labels_to_remove: list, user_id: str = 'me') -> dict:
    """
    Modifica os rótulos de uma mensagem no Gmail.

    Args:
        message_id (str): ID da mensagem.
        labels_to_add (list): Lista de IDs de rótulos a adicionar.
        labels_to_remove (list): Lista de IDs de rótulos a remover.
        user_id (str): ID do usuário (use 'me' para o usuário atual).

    Returns:
        dict: Resultado da operação.
    """
    print("⚙️ Executando função: modify_labels")
    service = authenticate_gmail()
    body = {
        'addLabelIds': labels_to_add,
        'removeLabelIds': labels_to_remove
    }
    result = service.users().messages().modify(
        userId=user_id, id=message_id, body=body).execute()
    return result


if __name__ == "__main__":
    # Initialize and run the server
    mcp.run(transport='stdio')
