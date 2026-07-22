"""Carregamento e gerenciamento de variáveis de ambiente."""
from __future__ import annotations
import os
from dataclasses import dataclass
from pathlib import Path
from dotenv import load_dotenv

RAIZ_PROJETO = Path(__file__).resolve().parent.parent

@dataclass(frozen=True)
class Config:
    """Configurações da aplicação carregadas a partir do ambiente."""
    caminho_planilha_entrada: Path
    caminho_saida_relatorio: Path
    caminho_base_referencia: Path | None
    log_level: str
    
    # Configurações BotCity Maestro
    maestro_enabled: bool
    vault_enabled: bool
    maestro_server_url: str
    maestro_api_key: str
    data_pool_name: str
    credential_label: str

    @classmethod
    def carregar(cls, env_path: Path | None = None) -> Config:
        caminho_env = env_path or RAIZ_PROJETO / ".env"
        load_dotenv(caminho_env)
        base_ref = os.getenv("CAMINHO_BASE_REFERENCIA", "").strip()
        
        return cls(
            caminho_planilha_entrada=Path(os.getenv("CAMINHO_PLANILHA_ENTRADA", "dados_entrada/planilha_lotes.xlsx")),
            caminho_saida_relatorio=Path(os.getenv("CAMINHO_SAIDA_RELATORIO", "logs/divergencias.xlsx")),
            caminho_base_referencia=Path(base_ref) if base_ref else None,
            log_level=os.getenv("LOG_LEVEL", "INFO").upper(),
            
            maestro_enabled=os.getenv("MAESTRO_ENABLED", "false").lower() == "true",
            vault_enabled=os.getenv("VAULT_ENABLED", "false").lower() == "true",
            maestro_server_url=os.getenv("MAESTRO_SERVER_URL", "https://maestro.botcity.dev"),
            maestro_api_key=os.getenv("MAESTRO_API_KEY", ""),
            data_pool_name=os.getenv("DATA_POOL_NAME", "FilaConferenciaLotes"),
            credential_label=os.getenv("CREDENTIAL_LABEL", "credencial_erp"),
        )
