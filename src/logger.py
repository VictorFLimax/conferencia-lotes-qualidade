import os
import logging
from pythonjsonlogger import json

# Recupera as variáveis de ambiente 
EXECUTION_ID = os.getenv("EXECUTION_ID", "local-dev")
BOT_ID = os.getenv("BOT_ID", "bot-test")

# Configura o formatador JSON
formatter = json.JsonFormatter(
    fmt="%(asctime)s %(levelname)s %(name)s %(message)s"
)

# Configura o Handler de saída 
handler = logging.StreamHandler()
handler.setFormatter(formatter)

# Cria o logger e adiciona o handler
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.addHandler(handler)

# Adiciona o contexto global IDs em todas as mensagens
extra_context = {
    "execution_id": EXECUTION_ID,
    "bot_id": BOT_ID
}

# Uso do logger injetando o contexto no campo 'extra'
logger.info("Iniciando processamento...", extra=extra_context)
logger.info("Usuário autenticado com sucesso", extra=extra_context)
logger.error("Erro ao conectar ao banco de dados", extra=extra_context)