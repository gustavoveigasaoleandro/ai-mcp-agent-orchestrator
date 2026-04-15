from autogen_ext.models.azure import AzureAIChatCompletionClient
from azure.core.credentials import AzureKeyCredential
import os
from dotenv import load_dotenv
from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient
load_dotenv()

model_client = AzureAIChatCompletionClient(
    model="gpt-4.1",
    deployment_name="gpt-4.1",  # Exatamente como está nomeado no Azure
    endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),  # Ex: "https://sologvsl.cognitiveservices.azure.com/"
    credential=AzureKeyCredential(os.getenv("AZURE_OPENAI_API_KEY")),
    api_version="2024-12-01-preview",  # Versão compatível com GPT-4o
    model_info={
        "json_output": True,
        "function_calling": True,
        "structured_output": True,
        "vision": True,
        "family": "gpt-4",
    },
    max_tokens=5000,
)

project_client = AIProjectClient(
    endpoint=os.getenv("PROJECT_ENDPOINT"),
    credential=DefaultAzureCredential()
)