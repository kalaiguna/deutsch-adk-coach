"""Voice note handling for Telegram .ogg Opus audio files.

Note: ConversationAgent currently uses types.Part.from_bytes() directly, which
supersedes prepare_telegram_voice_part(). This module is a placeholder for any
future pre-processing logic (e.g. resampling, format conversion) before the bytes
reach Gemini.
"""
import logging
from io import BytesIO

logger = logging.getLogger(__name__)

def prepare_telegram_voice_part(audio_bytes: bytes, mime_type: str = "audio/ogg") -> dict:
    """Prepares Telegram voice note bytes for Gemini Multimodal API.
    
    Gemini natively supports audio/ogg with Opus codec.
    """
    logger.info("Prepared audio payload of size %d bytes, mime: %s", len(audio_bytes), mime_type)
    return {
        "mime_type": mime_type,
        "data": audio_bytes
    }
