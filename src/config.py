"""Carregamento e gerenciamento de variáveis de ambiente."""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

RAIZ_PROJETO = Path(__file__).resolve().parent.parent


def _as_bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "sim", "on"}


def _resolve_path(raw: str) -> Path:
    caminho = Path(raw)
    if not caminho.is_absolute():
        caminho = RAIZ_PROJETO / caminho
    return caminho


def _normalizar_url(raw: str, default_path: str = "html/login.html") -> str:
    """
    Aceita URL http(s)/file:// ou caminho de arquivo (relativo ao projeto).

    Caminhos são convertidos em file:// para funcionar em qualquer máquina.
    Se o arquivo configurado não existir, tenta fallbacks conhecidos.
    """
    valor = (raw or "").strip()
    if not valor:
        valor = default_path

    if valor.startswith(("http://", "https://", "file://")):
        return valor

    caminho = _resolve_path(valor)
    if caminho.exists():
        return caminho.as_uri()

    # Fallbacks: login.html → lote-teste.html
    for candidato in (
        RAIZ_PROJETO / "html" / "login.html",
        RAIZ_PROJETO / "html" / "lote-teste.html",
        RAIZ_PROJETO / "web" / "lote-teste.html",
    ):
        if candidato.exists():
            return candidato.as_uri()

    # Mantém o URI esperado para o log apontar o caminho faltante
    return caminho.as_uri()


@dataclass(frozen=True)
class Config:
    """Configurações da aplicação carregadas a partir do .env."""

    caminho_planilha_entrada: Path
    caminho_saida_relatorio: Path
    caminho_base_referencia: Path | None
    log_file: Path
    log_level: str

    # BotCity Maestro
    maestro_enabled: bool
    vault_enabled: bool
    maestro_server_url: str
    maestro_login: str
    maestro_api_key: str
    data_pool_name: str
    credential_label: str

    # Automação web (Playwright | Selenium)
    web_automation_enabled: bool
    web_automation_driver: str
    web_automation_url: str
    web_form_url: str  # <-- ADICIONADO: URL do formulário/lotes
    playwright_headless: bool
    playwright_auto_install: bool
    selenium_headless: bool
    web_usuario: str
    web_senha: str

    # Screenshots / Result Files (Maestro Artifacts)
    screenshot_enabled: bool
    upload_artifacts: bool

    # Execution Log no Orchestrator
    execution_log_label: str

    # Arquivo de configuração efetivamente usado
    env_file: Path

    @classmethod
    def carregar(cls, env_path: Path | None = None) -> Config:
        caminho_env = env_path or RAIZ_PROJETO / ".env"
        # No Runner do BotCity o .env não é enviado no ZIP; usa o padrão embarcado
        if not caminho_env.exists():
            embarcado = RAIZ_PROJETO / ".env.botcity"
            if embarcado.exists():
                caminho_env = embarcado
        # override=False: parâmetros da task (os.environ) têm prioridade
        load_dotenv(caminho_env, override=False)

        # Compatível com INPUT_FILE (uso atual) e CAMINHO_PLANILHA_ENTRADA (legado)
        planilha = os.getenv("INPUT_FILE") or os.getenv(
            "CAMINHO_PLANILHA_ENTRADA", "dados_entrada/inspecao_lotes_dia.xlsx"
        )
        base_ref = os.getenv("CAMINHO_BASE_REFERENCIA", "").strip()
        log_file = os.getenv("LOG_FILE", "logs/execucao.log")
        driver = os.getenv("WEB_AUTOMATION_DRIVER", "playwright").strip().lower()
        if driver not in {"playwright", "selenium"}:
            raise ValueError(
                f"WEB_AUTOMATION_DRIVER inválido: '{driver}'. Use 'playwright' ou 'selenium'."
            )

        return cls(
            caminho_planilha_entrada=_resolve_path(planilha),
            caminho_saida_relatorio=_resolve_path(
                os.getenv("CAMINHO_SAIDA_RELATORIO", "logs/divergencias.xlsx")
            ),
            caminho_base_referencia=_resolve_path(base_ref) if base_ref else None,
            log_file=_resolve_path(log_file),
            log_level=os.getenv("LOG_LEVEL", "INFO").upper(),
            maestro_enabled=_as_bool(os.getenv("MAESTRO_ENABLED"), default=True),
            vault_enabled=_as_bool(os.getenv("VAULT_ENABLED"), default=False),
            maestro_server_url=os.getenv(
                "MAESTRO_SERVER_URL", "https://maestro.botcity.dev"
            ).rstrip("/"),
            maestro_login=os.getenv("MAESTRO_LOGIN", "").strip(),
            maestro_api_key=os.getenv("MAESTRO_API_KEY")
            or os.getenv("MAESTRO_KEY", ""),
            data_pool_name=os.getenv("DATA_POOL_NAME", "FilaConferenciaLotes_Eq_AGMV"),
            credential_label=os.getenv("CREDENTIAL_LABEL", "credencial_erp"),
            web_automation_enabled=_as_bool(
                os.getenv("WEB_AUTOMATION_ENABLED"), default=False
            ),
            web_automation_driver=driver,
            web_automation_url=_normalizar_url(
                os.getenv("WEB_AUTOMATION_URL", ""), default_path="html/login.html"
            ),
            web_form_url=_normalizar_url(
                os.getenv("WEB_FORM_URL", ""), default_path="html/lote-teste.html"
            ),  # <-- ADICIONADO
            playwright_headless=_as_bool(os.getenv("PLAYWRIGHT_HEADLESS"), default=False),
            playwright_auto_install=_as_bool(
                os.getenv("PLAYWRIGHT_AUTO_INSTALL"), default=True
            ),
            selenium_headless=_as_bool(os.getenv("SELENIUM_HEADLESS"), default=False),
            web_usuario=os.getenv("WEB_USUARIO", "usuario.teste"),
            web_senha=os.getenv("WEB_SENHA", "senha.teste"),
            screenshot_enabled=_as_bool(os.getenv("SCREENSHOT_ENABLED"), default=True),
            upload_artifacts=_as_bool(os.getenv("UPLOAD_ARTIFACTS"), default=True),
            execution_log_label=os.getenv(
                "EXECUTION_LOG_LABEL", "ConferenciaLotes_Execucao"
            ).strip()
            or "ConferenciaLotes_Execucao",
            env_file=caminho_env,
        )