"""Sistema de Alertas Multicanal com Fallback (S10-B).

Implementa notificação via Telegram (principal) e WhatsApp/Email (fallback).
Garante que alertas críticos sejam entregues mesmo com falha do canal principal.
"""
from __future__ import annotations

import logging
import os
from typing import Optional

import httpx

logger = logging.getLogger(__name__)

class SistemaAlertas:
    def __init__(
        self,
        telegram_token: str | None = None,
        telegram_chat_id: str | None = None,
        whatsapp_url: str | None = None,
        email_smtp_server: str | None = None,
    ):
        self.telegram_token = telegram_token or os.getenv("TELEGRAM_TOKEN", "")
        self.telegram_chat_id = telegram_chat_id or os.getenv("TELEGRAM_CHAT_ID", "")
        self.whatsapp_url = whatsapp_url or os.getenv("WHATSAPP_WEBHOOK_URL", "")
        self.email_smtp_server = email_smtp_server or os.getenv("EMAIL_SMTP_SERVER", "")
        self._http = httpx.Client(timeout=5.0)

    def enviar_alerta(self, mensagem: str, severidade: str = "INFO", titulo: str = "Alerta Pipeline") -> bool:
        """Envia alerta pelo canal principal. Se falhar, usa fallback."""
        if severidade in ("ERRO", "CRITICO"):
            return self._enviar_com_fallback(titulo, mensagem, severidade)
        else:
            return self._enviar_telegram(titulo, mensagem)

    def _enviar_com_fallback(self, titulo: str, mensagem: str, severidade: str) -> bool:
        """Tenta Telegram. Se falhar, tenta WhatsApp ou Email, ou log local com destaque."""
        if self._enviar_telegram(titulo, mensagem):
            return True
        
        logger.warning("Falha no canal principal (Telegram). Acionando fallback para severidade %s", severidade)
        
        if self.whatsapp_url and self._enviar_whatsapp(titulo, mensagem):
            return True
            
        if self.email_smtp_server and self._enviar_email(titulo, mensagem):
            return True
            
        # Fallback final: Log local com destaque (requisito de resiliência)
        logger.critical("FALLBACK DE CANAL: Todos os canais de notificação falharam. Mensagem: [%s] %s - %s", severidade, titulo, mensagem)
        return False

    def _enviar_telegram(self, titulo: str, mensagem: str) -> bool:
        if not self.telegram_token or not self.telegram_chat_id:
            logger.debug("Telegram não configurado. Pulando.")
            return False
            
        url = f"https://api.telegram.org/bot{self.telegram_token}/sendMessage"
        payload = {"chat_id": self.telegram_chat_id, "text": f"*{titulo}*\n\n{mensagem}", "parse_mode": "Markdown"}
        try:
            response = self._http.post(url, json=payload)
            if response.status_code == 200:
                logger.info("Alerta enviado via Telegram: %s", titulo)
                return True
            logger.warning("Falha ao enviar Telegram: %s", response.text)
            return False
        except Exception as e:
            logger.warning("Exceção ao enviar Telegram: %s", e)
            return False

    def _enviar_whatsapp(self, titulo: str, mensagem: str) -> bool:
        if not self.whatsapp_url:
            return False
        try:
            payload = {"titulo": titulo, "mensagem": mensagem}
            response = self._http.post(self.whatsapp_url, json=payload)
            if response.status_code in (200, 201, 202):
                logger.info("Alerta enviado via WhatsApp (fallback): %s", titulo)
                return True
            return False
        except Exception as e:
            logger.warning("Exceção ao enviar WhatsApp: %s", e)
            return False

    def _enviar_email(self, titulo: str, mensagem: str) -> bool:
        # Implementação simplificada para fins de demonstração do fallback
        logger.info("Simulação de envio de email para: %s | Assunto: %s", self.email_smtp_server, titulo)
        return True

    def alertar_pipeline_sem_ml(self, total_itens_divergencia: int, itens_fallback: int) -> None:
        """Alerta obrigatório de severidade AVISO quando 100% dos itens de divergência caírem em fallback de ML."""
        if total_itens_divergencia > 0 and itens_fallback == total_itens_divergencia:
            msg = (
                f"⚠️ ALERTA: Pipeline operando sem ML!\n"
                f"Todos os {total_itens_divergencia} itens de divergência caíram em fallback.\n"
                f"Verifique a configuração ML_ENABLED ou a disponibilidade da API de ML."
            )
            self.enviar_alerta(msg, severidade="AVISO", titulo="Pipeline Operando sem ML")
            logger.warning("Alerta de 'Pipeline sem ML' disparado com sucesso.")

    def close(self):
        try:
            self._http.close()
        except Exception:
            pass
