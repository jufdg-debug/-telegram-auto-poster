"""
Cliente simples da Bot API oficial do Telegram.
Usa apenas requests – sem bibliotecas pesadas.
Nunca loga o token.
"""

from __future__ import annotations

import logging
import os
import time
from typing import Optional

import requests

from config import (
    TELEGRAM_BOT_TOKEN,
    TELEGRAM_CHAT_ID,
    CAPTION_TEMPLATE,
    MAX_FILE_SIZE_MB,
    REQUEST_TIMEOUT,
)

logger = logging.getLogger(__name__)

API_BASE = "https://api.telegram.org"


class TelegramError(Exception):
    pass


def _api_url(method: str) -> str:
    if not TELEGRAM_BOT_TOKEN:
        raise TelegramError("TELEGRAM_BOT_TOKEN não configurado")
    return f"{API_BASE}/bot{TELEGRAM_BOT_TOKEN}/{method}"


def _handle_response(resp: requests.Response) -> dict:
    try:
        data = resp.json()
    except Exception:
        raise TelegramError(f"Resposta inválida do Telegram (HTTP {resp.status_code})")

    if not data.get("ok"):
        description = data.get("description", "erro desconhecido")
        error_code = data.get("error_code")
        # Rate limit
        if error_code == 429:
            retry_after = data.get("parameters", {}).get("retry_after", 30)
            logger.warning("Rate limit do Telegram. Aguardando %s segundos...", retry_after)
            time.sleep(int(retry_after) + 1)
            raise TelegramError(f"Rate limit: retry after {retry_after}s")
        raise TelegramError(f"Telegram API error {error_code}: {description}")
    return data.get("result", {})


def send_video(
    file_path: str,
    title: str = "",
    caption: Optional[str] = None,
    supports_streaming: bool = True,
) -> dict:
    """
    Envia um arquivo de vídeo para o chat configurado.
    Prefere sendVideo. Se o arquivo for grande demais ou falhar,
    tenta como documento.
    """
    if not os.path.isfile(file_path):
        raise TelegramError(f"Arquivo não encontrado: {file_path}")

    size_mb = os.path.getsize(file_path) / (1024 * 1024)
    if size_mb > MAX_FILE_SIZE_MB:
        raise TelegramError(
            f"Arquivo muito grande ({size_mb:.1f} MB). Limite configurado: {MAX_FILE_SIZE_MB} MB"
        )

    if caption is None:
        caption = CAPTION_TEMPLATE.format(title=title or "Sem título")

    # Telegram caption limit ~1024 chars
    if len(caption) > 1024:
        caption = caption[:1020] + "..."

    logger.info("Enviando vídeo para Telegram (%.1f MB)...", size_mb)

    url = _api_url("sendVideo")
    data = {
        "chat_id": TELEGRAM_CHAT_ID,
        "caption": caption,
        "supports_streaming": str(supports_streaming).lower(),
    }

    try:
        with open(file_path, "rb") as f:
            files = {"video": f}
            resp = requests.post(
                url,
                data=data,
                files=files,
                timeout=REQUEST_TIMEOUT + 60,  # upload pode demorar mais
            )
        return _handle_response(resp)
    except TelegramError:
        raise
    except requests.RequestException as e:
        logger.warning("Falha ao enviar como vídeo: %s. Tentando como documento...", e)
        return send_document(file_path, title=title, caption=caption)


def send_document(
    file_path: str,
    title: str = "",
    caption: Optional[str] = None,
) -> dict:
    """Envia o arquivo como documento (fallback)."""
    if not os.path.isfile(file_path):
        raise TelegramError(f"Arquivo não encontrado: {file_path}")

    size_mb = os.path.getsize(file_path) / (1024 * 1024)
    if size_mb > MAX_FILE_SIZE_MB:
        raise TelegramError(
            f"Arquivo muito grande ({size_mb:.1f} MB). Limite: {MAX_FILE_SIZE_MB} MB"
        )

    if caption is None:
        caption = CAPTION_TEMPLATE.format(title=title or "Sem título")

    if len(caption) > 1024:
        caption = caption[:1020] + "..."

    logger.info("Enviando como documento (%.1f MB)...", size_mb)

    url = _api_url("sendDocument")
    data = {
        "chat_id": TELEGRAM_CHAT_ID,
        "caption": caption,
    }

    with open(file_path, "rb") as f:
        files = {"document": f}
        resp = requests.post(
            url,
            data=data,
            files=files,
            timeout=REQUEST_TIMEOUT + 60,
        )
    return _handle_response(resp)


def test_connection() -> bool:
    """Verifica se o token e o chat estão ok (getMe + getChat)."""
    try:
        resp = requests.get(_api_url("getMe"), timeout=15)
        me = _handle_response(resp)
        logger.info("Bot conectado: @%s", me.get("username", "?"))

        resp = requests.get(
            _api_url("getChat"),
            params={"chat_id": TELEGRAM_CHAT_ID},
            timeout=15,
        )
        chat = _handle_response(resp)
        logger.info("Chat encontrado: %s (id=%s)", chat.get("title") or chat.get("type"), TELEGRAM_CHAT_ID)
        return True
    except Exception as e:
        logger.error("Falha no teste de conexão Telegram: %s", e)
        return False
