"""
Módulo de Configuração Centralizada com Pydantic Settings.
Governança The DX Way - LG Electronics / AX Academy.
"""

from pathlib import Path
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class PipelineSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Identificação do Ambiente e Runner
    ENVIRONMENT: str = Field(default="development", description="development | staging | production")
    RUNNER_ID: str = Field(default="RUNNER_SMART_OFFICE_01", description="Identificador único do Runner")
    RUNNER_LOCK_FILE: str = Field(
        default="logs/runner_desktop_session.lock",
        description="Arquivo mutex para lock exclusivo de sessão gráfica desktop"
    )
    RUNNER_LOCK_TIMEOUT_SECONDS: int = Field(
        default=60,
        description="Tempo de expiração de um lock considerado órfão (stale lock)"
    )

    # Timeouts e Dependências do Orquestrador
    DEPENDENCY_TIMEOUT_SECONDS: float = Field(
        default=15.0,
        description="Deadline máximo de espera por predecessors no bot consolidador"
    )
    EXECUTION_MAX_RETRIES: int = Field(default=3, description="Máximo de retries para falhas de infra")
    RETRY_BACKOFF_FACTOR: float = Field(default=1.5, description="Fator multiplicador do backoff exponencial")

    # Feature Flag e Configuração de Machine Learning
    ML_ENABLED: bool = Field(default=True, description="Feature flag para ativação do enriquecimento de ML")
    ML_MIN_CONFIDENCE: float = Field(default=0.75, description="Limiar de confiança mínima para aceitar inferência")
    ML_API_URL: str = Field(default="http://127.0.0.1:8002", description="URL base do microserviço de ML")
    ML_TIMEOUT_SECONDS: float = Field(default=3.0, description="Timeout estrito para chamada do ML")

    # Mocks de Sistemas
    DESKTOP_APP_PATH: str = Field(
        default="mocks/desktop_app/app.py",
        description="Caminho do script da aplicação desktop legado"
    )
    WEB_PORTAL_URL: str = Field(
        default="http://127.0.0.1:8001",
        description="URL base do portal web de fornecedores"
    )

    # Notificações Multicanal
    TELEGRAM_ENABLED: bool = Field(default=True, description="Habilita canal Telegram")
    TELEGRAM_BOT_TOKEN: str = Field(default="", description="Token do bot do Telegram")
    TELEGRAM_CHAT_ID: str = Field(default="", description="Chat ID de destino no Telegram")

    EMAIL_ENABLED: bool = Field(default=True, description="Habilita canal de contingência de email")
    EMAIL_SMTP_SERVER: str = Field(default="smtp.exemplo.com", description="Servidor SMTP para contingência")
    EMAIL_DESTINATARIO: str = Field(default="operacao_rpa@lge.com", description="Destinatário dos alertas")

    # Diretórios de Dados e Auditoria
    LOG_DIR: Path = Field(default=Path("logs"), description="Diretório de logs estruturados")
    DATA_OUTPUT_DIR: Path = Field(default=Path("output"), description="Diretório de relatórios gerados")
    DLQ_STORAGE_PATH: Path = Field(
        default=Path("logs/dead_letter_queue.json"),
        description="Armazenamento auditável de itens na DLQ"
    )


# Instância global das configurações
settings = PipelineSettings()
