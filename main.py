#!/usr/bin/env python3
"""
Ponto de entrada do telegram-auto-poster.

Fluxo:
1. Carrega configuração e fontes
2. Para cada fonte, busca candidatos
3. Filtra os que já foram publicados
4. Baixa (quando media_url legítima existe)
5. Envia para o Telegram (ou só simula se DRY_RUN)
6. Registra no estado
"""

from __future__ import annotations

import logging
import os
import shutil
import sys
import tempfile
from pathlib import Path
from typing import List

import requests

from config import (
    DRY_RUN,
    MAX_VIDEOS_PER_RUN,
    MAX_FILE_SIZE_MB,
    DOWNLOAD_DIR,
    DOWNLOAD_TIMEOUT,
    REQUEST_TIMEOUT,
    SOURCES,
    TELEGRAM_BOT_TOKEN,
    TELEGRAM_CHAT_ID,
)
from database import is_published, mark_published, get_published_ids
from sources import get_all_sources, VideoItem
from telegram_client import send_video, TelegramError, test_connection

# ------------------------------------------------------------
# Logging
# ------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="[%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("auto_poster")


def _safe_filename(content_id: str) -> str:
    """Gera nome de arquivo seguro a partir do content_id."""
    safe = "".join(c if c.isalnum() or c in "-_" else "_" for c in content_id)
    return safe[:80] or "video"


def download_video(item: VideoItem, dest_dir: str) -> str | None:
    """
    Baixa o vídeo apenas se media_url existir e for acessível.
    Retorna o caminho local ou None em caso de falha.
    Nunca tenta contornar proteções.
    """
    if not item.media_url:
        logger.warning("Item %s não possui media_url – pulando download", item.content_id)
        return None

    # Checagem rápida de tamanho via HEAD (quando o servidor suporta)
    try:
        head = requests.head(
            item.media_url,
            timeout=REQUEST_TIMEOUT,
            allow_redirects=True,
            headers={"User-Agent": "telegram-auto-poster/1.0 (authorized-test)"},
        )
        content_length = head.headers.get("Content-Length")
        if content_length:
            size_mb = int(content_length) / (1024 * 1024)
            if size_mb > MAX_FILE_SIZE_MB:
                logger.warning(
                    "Arquivo remoto muito grande (%.1f MB > %d MB): %s",
                    size_mb,
                    MAX_FILE_SIZE_MB,
                    item.content_id,
                )
                return None
    except requests.RequestException as e:
        logger.debug("HEAD falhou (continuando com GET): %s", e)

    filename = _safe_filename(item.content_id) + ".mp4"
    dest_path = os.path.join(dest_dir, filename)

    logger.info("Baixando: %s", item.media_url)
    try:
        with requests.get(
            item.media_url,
            stream=True,
            timeout=DOWNLOAD_TIMEOUT,
            headers={"User-Agent": "telegram-auto-poster/1.0 (authorized-test)"},
        ) as r:
            r.raise_for_status()
            # Verifica content-type grosseiramente
            ctype = r.headers.get("Content-Type", "").lower()
            if ctype and not any(x in ctype for x in ("video", "octet-stream", "mp4", "application")):
                logger.warning("Content-Type suspeito (%s) para %s", ctype, item.content_id)

            total = 0
            max_bytes = MAX_FILE_SIZE_MB * 1024 * 1024
            with open(dest_path, "wb") as f:
                for chunk in r.iter_content(chunk_size=64 * 1024):
                    if not chunk:
                        continue
                    total += len(chunk)
                    if total > max_bytes:
                        logger.warning("Download excedeu limite de tamanho – abortando")
                        f.close()
                        os.remove(dest_path)
                        return None
                    f.write(chunk)

        if total < 1024:  # menos de 1 KB provavelmente inválido
            logger.warning("Arquivo baixado muito pequeno (%d bytes) – descartando", total)
            os.remove(dest_path)
            return None

        logger.info("Download concluído: %.1f MB", total / (1024 * 1024))
        return dest_path

    except requests.RequestException as e:
        logger.error("Falha no download de %s: %s", item.content_id, e)
        if os.path.exists(dest_path):
            os.remove(dest_path)
        return None


def process_item(item: VideoItem, source_name: str) -> bool:
    """
    Processa um único item: download → envio → registro.
    Retorna True se foi publicado (ou simulado com sucesso).
    """
    if is_published(item.content_id):
        logger.info("Conteúdo já publicado: ignorando (%s)", item.content_id)
        return False

    logger.info("Conteúdo novo encontrado: %s – %s", item.content_id, item.title)

    if DRY_RUN:
        logger.info(
            "[DRY_RUN] Seria publicado: id=%s title=%r media=%s",
            item.content_id,
            item.title,
            item.media_url,
        )
        # Em dry-run ainda registramos para não repetir na próxima execução de teste
        # (pode comentar a linha abaixo se quiser que dry-run não marque)
        # mark_published(item.content_id, title=item.title, source=source_name)
        return True

    # Download
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    local_path = download_video(item, DOWNLOAD_DIR)
    if not local_path:
        logger.error("Não foi possível obter o arquivo de %s", item.content_id)
        return False

    try:
        send_video(local_path, title=item.title)
        logger.info("Publicado com sucesso: %s", item.content_id)
        mark_published(
            item.content_id,
            title=item.title,
            source=source_name,
            extra={"page_url": item.page_url},
        )
        return True
    except TelegramError as e:
        logger.error("Erro ao enviar para Telegram: %s", e)
        return False
    finally:
        # Limpa o arquivo local
        try:
            if os.path.exists(local_path):
                os.remove(local_path)
        except OSError:
            pass


def run() -> int:
    logger.info("Iniciando execução")
    logger.info("DRY_RUN=%s | MAX_VIDEOS_PER_RUN=%d | CHAT_ID=%s", DRY_RUN, MAX_VIDEOS_PER_RUN, TELEGRAM_CHAT_ID)

    if not TELEGRAM_BOT_TOKEN and not DRY_RUN:
        logger.error("TELEGRAM_BOT_TOKEN não definido e DRY_RUN=false. Abortando.")
        return 1

    if not DRY_RUN:
        if not test_connection():
            logger.error("Não foi possível validar a conexão com o Telegram. Abortando.")
            return 1

    published_before = get_published_ids()
    logger.info("Itens já registrados: %d", len(published_before))

    sources = get_all_sources(SOURCES)
    if not sources:
        logger.warning("Nenhuma fonte configurada.")
        return 0

    sent_count = 0

    for source in sources:
        if sent_count >= MAX_VIDEOS_PER_RUN:
            logger.info("Limite de vídeos por execução atingido (%d)", MAX_VIDEOS_PER_RUN)
            break

        logger.info("Verificando fonte: %s", source.name)
        try:
            candidates: List[VideoItem] = source.fetch_new_items()
        except Exception as e:
            logger.error("Erro ao buscar itens da fonte %s: %s", source.name, e)
            continue

        for item in candidates:
            if sent_count >= MAX_VIDEOS_PER_RUN:
                break
            try:
                if process_item(item, source.name):
                    sent_count += 1
            except Exception as e:
                logger.exception("Erro inesperado ao processar %s: %s", item.content_id, e)

    # Limpeza do diretório de downloads
    if os.path.isdir(DOWNLOAD_DIR):
        try:
            shutil.rmtree(DOWNLOAD_DIR, ignore_errors=True)
        except Exception:
            pass

    logger.info("Execução concluída. Publicados nesta run: %d", sent_count)
    return 0


if __name__ == "__main__":
    sys.exit(run())
