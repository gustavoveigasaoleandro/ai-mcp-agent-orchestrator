from datetime import datetime
from pathlib import Path

from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

SCOPES = ['https://www.googleapis.com/auth/spreadsheets',
          'https://www.googleapis.com/auth/drive.file'
          ]
BASE_DIR = Path(__file__).resolve().parent
TOKEN_PATH = BASE_DIR / "token.json"
CREDENTIALS_PATH = BASE_DIR / "credentials.json"


def authenticate_sheets() -> object:
    """
    Autentica com a API do sheets e retorna um serviço autenticado.

    Returns:
        object: Objeto de serviço autenticado da API sheets.
    """
    print("⚙️ Executando função: authenticate_sheets")
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
    service = build('sheets', 'v4', credentials=creds, cache_discovery=False)
    return service


# Permite execução direta do script para testar autenticação com Google Sheets
if __name__ == "__main__":
    service = authenticate_sheets()
    print("✅ Serviço do Google Sheets autenticado com sucesso:", service)
