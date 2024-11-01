from typing import Dict, Optional
import vosk
import json
from .base import BaseRecognizer
from ....core.config import RECOGNITION_CONTEXTS
from omni.utils.logging import get_logger

class VoskRecognizer(BaseRecognizer):
    def __init__(self):
        self._model = None
        self._recognizer = None
        self._current_context = None
        self._logger = get_logger(__name__)

    async def initialize(self) -> None:
        try:
            model_path = "./vosk-model-small-en-us-0.15"
            self._model = vosk.Model(model_path)
            self._logger.info("Vosk recognizer initialized")
        except Exception as e:
            self._logger.error(f"Failed to initialize Vosk: {e}")
            raise

    async def recognize(self, context: Optional[str] = None) -> Dict[str, any]:
        try:
            if context:
                self._current_context = context

            # Perform basic recognition
            # ... existing Vosk recognition code ...
            recognized_text = "example text"  # Replace with actual recognition

            # Apply context-based corrections if context is set
            if self._current_context:
                recognized_text = self._apply_context_corrections(recognized_text)

            return {
                "text": recognized_text,
                "context": self._current_context,
                "success": True
            }

        except Exception as e:
            self._logger.error(f"Recognition error: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def _apply_context_corrections(self, text: str) -> str:
        """Apply context-specific corrections to recognized text."""
        if not text or not self._current_context:
            return text

        context_data = RECOGNITION_CONTEXTS.get(self._current_context)
        if not context_data:
            return text

        text_lower = text.lower()
        has_context = any(keyword in text_lower 
                         for keyword in context_data['keywords'])

        if has_context:
            for wrong, correct in context_data['patterns']:
                if wrong in text_lower:
                    self._logger.debug(
                        f"Correcting '{wrong}' to '{correct}' "
                        f"[context: {self._current_context}]"
                    )
                    text = text_lower.replace(wrong, correct)

        return text

    async def cleanup(self) -> None:
        if self._recognizer:
            self._recognizer = None
        if self._model:
            self._model = None
