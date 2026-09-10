"""
Fonte do tipo "lista".

Use esta fonte quando você tiver links diretos de vídeos
que você tem autorização para baixar e redistribuir.

Como usar no config.py:

SOURCES = [
    {
        "type": "lista",
        "name": "Meus vídeos autorizados",
        "max_items": 3,
        "videos": [
            {
                "id": "video-001",
                "title": "Título do vídeo 1",
                "url": "https://exemplo.com/video1.mp4",
            },
            {
                "id": "video-002",
                "title": "Título do vídeo 2",
                "url": "https://exemplo.com/video2.mp4",
            },
        ],
    },
]
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List

from sources.base import BaseSource, VideoItem

logger = logging.getLogger(__name__)


class ListSource(BaseSource):
    """Fonte baseada em uma lista de links diretos autorizados."""

    def __init__(self, config: Dict[str, Any]) -> None:
        super().__init__(config)
        self.videos: List[Dict[str, Any]] = config.get("videos", [])

    def fetch_new_items(self) -> List[VideoItem]:
        logger.info("[%s] Carregando lista de vídeos autorizados (%d itens)...", self.name, len(self.videos))

        items: List[VideoItem] = []

        for raw in self.videos[: self.max_items]:
            try:
                content_id = str(raw.get("id") or raw.get("url") or "").strip()
                title = str(raw.get("title") or "Vídeo sem título").strip()
                media_url = str(raw.get("url") or "").strip()

                if not content_id or not media_url:
                    logger.warning("[%s] Item inválido ignorado (faltando id ou url): %s", self.name, raw)
                    continue

                if not media_url.startswith(("http://", "https://")):
                    logger.warning("[%s] URL inválida ignorada: %s", self.name, media_url)
                    continue

                item = VideoItem(
                    content_id=content_id,
                    page_url=media_url,
                    title=title,
                    media_url=media_url,
                    extra={"source_type": "lista"},
                )
                items.append(item)

            except Exception as e:
                logger.warning("[%s] Erro ao processar item da lista: %s", self.name, e)

        logger.info("[%s] %d item(ns) candidato(s) encontrado(s)", self.name, len(items))
        return items
