"""
Configurações centralizadas do projeto.
Tudo que pode ser alterado sem mexer na lógica principal fica aqui
ou em variáveis de ambiente / Secrets do GitHub.
"""

import os
from typing import List, Dict, Any


def _bool_env(name: str, default: str = "false") -> bool:
    return os.getenv(name, default).strip().lower() in ("1", "true", "yes", "on")


def _int_env(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)))
    except (TypeError, ValueError):
        return default


# Telegram (obrigatórios em produção)
TELEGRAM_BOT_TOKEN: str | None = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID: str = os.getenv("TELEGRAM_CHAT_ID", "-1003634142944")

# Comportamento
DRY_RUN: bool = _bool_env("DRY_RUN", "false")
MAX_VIDEOS_PER_RUN: int = _int_env("MAX_VIDEOS_PER_RUN", 2)

# Legenda (pode ser sobrescrita por variável de ambiente)
CAPTION_TEMPLATE: str = os.getenv(
    "CAPTION_TEMPLATE",
    "🔥 Novo vídeo\n\n{title}",
)

# Limites de segurança
MAX_FILE_SIZE_MB: int = _int_env("MAX_FILE_SIZE_MB", 45)  # abaixo do limite de 50 MB do Telegram
REQUEST_TIMEOUT: int = _int_env("REQUEST_TIMEOUT", 60)
DOWNLOAD_TIMEOUT: int = _int_env("DOWNLOAD_TIMEOUT", 120)

# Caminho do arquivo de estado (publicado)
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
PUBLISHED_FILE = os.path.join(DATA_DIR, "published.json")

# Diretório temporário de downloads (limpo a cada execução)
DOWNLOAD_DIR = os.path.join(os.path.dirname(__file__), "downloads")

# ------------------------------------------------------------
# FONTES
# Adicione ou remova fontes aqui.
# Cada item é um dicionário com pelo menos "type" e "name".
# Tipos disponíveis no momento: "example" (seguro para testes)
# ------------------------------------------------------------
SOURCES: List[Dict[str, Any]] = [
    {
        "type": "example",
        "name": "Exemplo Seguro (vídeos de teste públicos)",
        # Opcional: limite de itens por fonte nesta execução
        "max_items": 2,
    },
    # Exemplo de como adicionar uma futura fonte autorizada:
    # {
    #     "type": "generic",          # ou o nome do seu adaptador
    #     "name": "Minha Fonte Autorizada",
    #     "base_url": "https://exemplo.com/feed",
    #     "max_items": 3,
    # },
]
