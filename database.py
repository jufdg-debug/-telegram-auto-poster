"""
Controle de duplicatas usando um arquivo JSON simples.
Funciona bem com GitHub Actions (o workflow faz commit do arquivo quando há mudanças).
"""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone
from typing import Dict, Set

from config import DATA_DIR, PUBLISHED_FILE

logger = logging.getLogger(__name__)


def _ensure_data_dir() -> None:
    os.makedirs(DATA_DIR, exist_ok=True)


def load_published() -> Dict[str, dict]:
    """Retorna dicionário {content_id: {title, source, published_at, ...}}."""
    _ensure_data_dir()
    if not os.path.exists(PUBLISHED_FILE):
        return {}
    try:
        with open(PUBLISHED_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict):
            return data
        logger.warning("Formato inesperado em published.json – reiniciando estado.")
        return {}
    except (json.JSONDecodeError, OSError) as e:
        logger.error("Erro ao ler published.json: %s", e)
        return {}


def save_published(data: Dict[str, dict]) -> None:
    _ensure_data_dir()
    try:
        with open(PUBLISHED_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except OSError as e:
        logger.error("Erro ao salvar published.json: %s", e)
        raise


def is_published(content_id: str) -> bool:
    return content_id in load_published()


def mark_published(
    content_id: str,
    title: str = "",
    source: str = "",
    extra: dict | None = None,
) -> None:
    data = load_published()
    entry = {
        "title": title,
        "source": source,
        "published_at": datetime.now(timezone.utc).isoformat(),
    }
    if extra:
        entry.update(extra)
    data[content_id] = entry
    save_published(data)
    logger.info("Registrado como publicado: %s", content_id)


def get_published_ids() -> Set[str]:
    return set(load_published().keys())
