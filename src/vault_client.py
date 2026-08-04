"""Cliente de credenciais via Vault do BotCity Maestro."""
from __future__ import annotations

import logging

from botcity.maestro import BotMaestroSDK

from src.config import Config

logger = logging.getLogger(__name__)


def get_erp_credentials(maestro: BotMaestroSDK, config: Config) -> dict[str, str]:
    """
    Retorna credenciais do Vault (ou fallback local).

    Chaves retornadas: login, password.
    """
    if not config.vault_enabled:
        logger.warning(
            "Vault desabilitado (VAULT_ENABLED=false). Usando WEB_USUARIO/WEB_SENHA."
        )
        return {"login": config.web_usuario, "password": config.web_senha}

    try:
        credential = maestro.get_credential(label=config.credential_label)
        if not credential:
            raise ValueError(
                f"Credencial '{config.credential_label}' não encontrada no Vault."
            )

        login = getattr(credential, "login", None) or credential.get("usuario") or credential.get("login")
        password = getattr(credential, "password", None) or credential.get("senha") or credential.get("password")

        # Alguns vaults retornam dict de chaves livres
        if login is None and isinstance(credential, dict):
            login = credential.get("usuario") or credential.get("login")
            password = credential.get("senha") or credential.get("password")

        if not login or not password:
            # API get_credential pode retornar objeto com .keys
            keys = getattr(credential, "keys", None)
            if keys and callable(keys) is False and isinstance(keys, dict):
                login = keys.get("usuario") or keys.get("login")
                password = keys.get("senha") or keys.get("password")

        if not login or not password:
            raise ValueError(
                f"Credencial '{config.credential_label}' sem chaves usuario/senha."
            )

        logger.info("Credencial Vault carregada. Usuário: %s", login)
        return {"login": str(login), "password": str(password)}
    except Exception as exc:
        logger.error("Erro ao recuperar credenciais do Vault: %s", exc)
        raise
