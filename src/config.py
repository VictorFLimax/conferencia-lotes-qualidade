import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    MAESTRO_ENABLED = os.getenv("MAESTRO_ENABLED", "false").lower() == "true"
    VAULT_ENABLED = os.getenv("VAULT_ENABLED", "false").lower() == "true"
    
    MAESTRO_SERVER_URL = os.getenv("MAESTRO_SERVER_URL", "https://maestro.botcity.dev")
    MAESTRO_API_KEY = os.getenv("MAESTRO_API_KEY", "")
    
    DATA_POOL_NAME = os.getenv("DATA_POOL_NAME", "FilaAuditoriaLotes")
    CREDENTIAL_LABEL = os.getenv("CREDENTIAL_LABEL", "credencial_erp")
    
    INPUT_FOLDER = os.getenv("INPUT_FOLDER", "dados_entrada")
    LOG_FILE = os.getenv("LOG_FILE", "logs/execucao.log")# config.py - Configurações da automação
