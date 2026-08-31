"""
Bot 05: Notificação e Relatórios com Rastreabilidade (LG_Notificador_Relatorio_V1).
Geração de relatórios de auditoria (.csv e .xlsx) e alertas multicanal com contingência.
Roteamento por severidade: INFO, WARN (modo degradado), CRITICAL (falha de infra/DLQ).
Fallback de canal: Telegram -> Email / Log de Contingência.
The DX Way.
"""

import csv
import logging
import time
from pathlib import Path
from typing import Any, Dict, List, Optional
import httpx
import pandas as pd
from core.config import settings

logger = logging.getLogger("bots.notifier_reporter")


class NotifierReporterBot:
    """
    Bot 05 - Responsável por gerar relatórios auditáveis e despachar notificações
    multicanal resilientes com roteamento de severidade.
    """

    def __init__(self, runner_id: Optional[str] = None):
        self.bot_id = "LG_Notificador_Relatorio_V1"
        self.runner_id = runner_id or settings.RUNNER_ID
        self.output_dir = Path("logs")
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def run(
        self,
        itens_classificados: List[Dict[str, Any]],
        degraded_mode: bool = False,
        dlq_count: int = 0,
        forced_telegram_token: Optional[str] = None,
    ) -> Dict[str, Any]:
        logger.info(f"[{self.bot_id}] Gerando relatórios de auditoria e emitindo alertas...")

        # 1. Geração dos Relatórios de Auditoria
        caminho_csv, caminho_xlsx = self._gerar_relatorios(itens_classificados)

        # 2. Definição da Severidade
        if dlq_count > 0:
            severidade = "CRITICAL"
            mensagem_resumo = f"ALERTA CRÍTICO: Execução com {dlq_count} itens na Dead Letter Queue!"
        elif degraded_mode:
            severidade = "WARN"
            mensagem_resumo = "ALERTA: Execução operou em Modo Degradado (fallback ativado)!"
        else:
            severidade = "INFO"
            mensagem_resumo = "Sucesso: Processamento regular diário concluído com êxito."

        # 3. Disparo Multicanal com Fallback
        canal_utilizado = self._disparar_notificacao_com_fallback(
            severidade=severidade,
            mensagem=f"{mensagem_resumo}\nTotal Itens: {len(itens_classificados)} | Runner: {self.runner_id}",
            arquivo_anexo=caminho_xlsx,
            forced_token=forced_telegram_token,
        )

        return {
            "bot_id": self.bot_id,
            "status": "COMPLETED",
            "relatorio_csv": str(caminho_csv),
            "relatorio_xlsx": str(caminho_xlsx),
            "severidade": severidade,
            "canal_notificacao_utilizado": canal_utilizado,
        }

    def _gerar_relatorios(self, itens: List[Dict[str, Any]]) -> (Path, Path):
        linhas_relatorio = []
        agora = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

        for idx, item in enumerate(itens):
            linhas_relatorio.append({
                "id_item": f"AUD_{idx+1:04d}",
                "cod_item": item.get("cod_item", ""),
                "descricao": item.get("descricao", ""),
                "estoque_fisico": item.get("estoque_fisico", 0),
                "qtd_solicitada": item.get("qtd_solicitada", 0),
                "status_regra": item.get("status_regra", ""),
                "causa_divergencia": item.get("causa_divergencia", ""),
                "origem_decisao": item.get("origem_decisao", "REGRA_DETERMINISTICA"),
                "confianca_ml": item.get("confianca_ml", 0.0),
                "timestamp": agora,
                "runner_id": self.runner_id,
            })

        df = pd.DataFrame(linhas_relatorio)

        caminho_csv = self.output_dir / "relatorio_auditoria.csv"
        caminho_xlsx = self.output_dir / "relatorio_auditoria.xlsx"

        df.to_csv(caminho_csv, index=False, encoding="utf-8-sig")
        df.to_excel(caminho_xlsx, index=False)

        logger.info(f"[{self.bot_id}] Relatórios gerados com sucesso: {caminho_csv} e {caminho_xlsx}")
        return caminho_csv, caminho_xlsx

    def _disparar_notificacao_com_fallback(
        self,
        severidade: str,
        mensagem: str,
        arquivo_anexo: Path,
        forced_token: Optional[str] = None
    ) -> str:
        """
        Dispara primeiro para o canal primário (Telegram).
        Em caso de erro (token inválido, rede fora), roteia para o canal secundário (Email/Log de Contingência).
        """
        token = forced_token if forced_token is not None else settings.TELEGRAM_BOT_TOKEN
        chat_id = settings.TELEGRAM_CHAT_ID

        # Tentativa no canal primário (Telegram)
        if settings.TELEGRAM_ENABLED and token and token.strip() != "":
            try:
                logger.info(f"[{self.bot_id}] Tentando notificação via Telegram (Canal Primário)...")
                self._enviar_telegram(token, chat_id, f"[{severidade}] {mensagem}")
                logger.info(f"[{self.bot_id}] Notificação enviada via Telegram com sucesso.")
                return "TELEGRAM_PRIMARY"
            except Exception as e:
                logger.warning(
                    f"[{self.bot_id}] FALHA NO CANAL PRIMÁRIO (Telegram): {e}. "
                    f"Acionando FALLBACK para Canal Secundário (Email/Contingência)..."
                )

        # Canal Secundário / Fallback (Email simulado ou Log de Contingência com destaque)
        logger.info(f"[{self.bot_id}] Despachando alerta via CANAL SECUNDÁRIO (Email Contingência)...")
        self._enviar_email_contingencia(severidade, mensagem, arquivo_anexo)
        return "EMAIL_FALLBACK_CONTINGENCY"

    def _enviar_telegram(self, token: str, chat_id: str, texto: str) -> None:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        with httpx.Client(timeout=4.0) as client:
            resp = client.post(url, json={"chat_id": chat_id, "text": texto})
            if resp.status_code != 200:
                raise RuntimeError(f"Telegram API retornou HTTP {resp.status_code}: {resp.text}")

    def _enviar_email_contingencia(self, severidade: str, mensagem: str, anexo: Path) -> None:
        # Gravação de alerta destacado em arquivo de contingência de auditoria
        arquivo_contingencia = self.output_dir / "contingencia_notificacoes.log"
        registro = (
            f"\n{'='*70}\n"
            f"[CANAL SECUNDÁRIO DE CONTINGÊNCIA - EMAIL SIMULADO]\n"
            f"Data/Hora: {time.strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"Servidor SMTP: {settings.EMAIL_SMTP_SERVER}\n"
            f"Destinatário: {settings.EMAIL_DESTINATARIO}\n"
            f"Severidade: {severidade}\n"
            f"Mensagem: {mensagem}\n"
            f"Anexo Auditado: {anexo.name} ({anexo.stat().st_size if anexo.exists() else 0} bytes)\n"
            f"{'='*70}\n"
        )
        with open(arquivo_contingencia, "a", encoding="utf-8") as f:
            f.write(registro)
        print(registro)
