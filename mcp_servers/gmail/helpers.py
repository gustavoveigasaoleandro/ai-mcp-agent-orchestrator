from datetime import datetime
from pathlib import Path

from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

SCOPES = ['https://www.googleapis.com/auth/gmail.modify']
BASE_DIR = Path(__file__).resolve().parent
TOKEN_PATH = BASE_DIR / "token.json"
CREDENTIALS_PATH = BASE_DIR / "credentials.json"


def format_date_gmail(dt: datetime) -> str:
    """Converte datetime para o formato usado pelo Gmail: yyyy/mm/dd."""
    return dt.strftime('%Y/%m/%d')


def authenticate_gmail() -> object:
    """
    Autentica com a API do Gmail e retorna um serviço autenticado.

    Returns:
        object: Objeto de serviço autenticado da API Gmail.
    """
    print("⚙️ Executando função: authenticate_gmail")
    creds = None
    if TOKEN_PATH.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_PATH), SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(str(CREDENTIALS_PATH), SCOPES)
            creds = flow.run_local_server(port=0)
        with TOKEN_PATH.open('w') as token:
            token.write(creds.to_json())
    service = build('gmail', 'v1', credentials=creds, cache_discovery=False)
    return service
