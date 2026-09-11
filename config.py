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
# Telegram Bot API hard limit is 50 MB. We stay just under it.
MAX_FILE_SIZE_MB: int = _int_env("MAX_FILE_SIZE_MB", 49)
REQUEST_TIMEOUT: int = _int_env("REQUEST_TIMEOUT", 60)
DOWNLOAD_TIMEOUT: int = _int_env("DOWNLOAD_TIMEOUT", 180)

# Caminho do arquivo de estado (publicado)
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
PUBLISHED_FILE = os.path.join(DATA_DIR, "published.json")

# Diretório temporário de downloads (limpo a cada execução)
DOWNLOAD_DIR = os.path.join(os.path.dirname(__file__), "downloads")

# ------------------------------------------------------------
# FONTES
# Adicione ou remova fontes aqui.
# Tipos disponíveis: "example", "lista", "generic", "erome"
# ------------------------------------------------------------
SOURCES: List[Dict[str, Any]] = [
    # Fonte de exemplo (vídeos públicos de teste) - pode remover se não quiser mais
    # {
    #     "type": "example",
    #     "name": "Exemplo Seguro",
    #     "max_items": 2,
    # },

    # ============================================================
    # FONTE TIPO "lista" - coloque aqui seus vídeos autorizados
    # ============================================================
    {
        "type": "lista",
        "name": "Meus vídeos autorizados",
        "max_items": 3,
        "videos": [
            # Exemplo de como adicionar (substitua pelos seus links reais):
            # {
            #     "id": "video-001",                    # identificador único
            #     "title": "Título do vídeo",           # aparece na legenda
            #     "url": "https://exemplo.com/video.mp4",  # link DIRETO do arquivo
            # },
        ],
    },
]


# Links privados ficam nos Secrets, nunca no código.
EROME_URLS = os.getenv("EROME_URLS", "").strip()
if EROME_URLS:
    SOURCES.insert(0, {
        "type": "erome",
        "name": "Meus vídeos do Erome",
        "urls": EROME_URLS,
        "max_items": max(20, MAX_VIDEOS_PER_RUN * 5),
        "max_pages": _int_env("EROME_MAX_PAGES", 10),
        "max_albums": _int_env("EROME_MAX_ALBUMS", 100),
    })
