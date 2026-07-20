# vault_client.py - Cliente de credenciais/vault
import logging
from botcity.maestro import BotMaestroSDK
from src.config import Config

logger = logging.getLogger(__name__)

def get_erp_credentials(maestro: BotMaestroSDK) -> dict:
    if not Config.VAULT_ENABLED:
        logger.warning("Vault desabilitado via .env. Usando credenciais fictícias para teste local.")
        return {"login": "usuario_teste", "password": "senha_ficticia"}
    
    try:
        credential = maestro.get_credential(label=Config.CREDENTIAL_LABEL)
        if not credential:
            raise ValueError(f"Credencial '{Config.CREDENTIAL_LABEL}' não encontrada no Vault.")
        
        # REGRA DE OURO: Logar apenas o usuário, NUNCA a senha
        logger.info(f"Acessando sistema com o usuário: {credential.login}")
        
        return {"login": credential.login, "password": credential.password}
    except Exception as e:
        logger.error(f"Erro ao recuperar credenciais do Vault: {e}")
        raise
