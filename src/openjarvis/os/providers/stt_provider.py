import os
import numpy as np
from typing import AsyncIterator
from .base import STTProvider

class LocalSTTProvider(STTProvider):
    def __init__(self, model_size: str = "base"):
        try:
            from faster_whisper import WhisperModel
            self.model = WhisperModel(model_size, device="cpu", compute_type="int8")
        except ImportError:
            self.model = None

    async def transcribe_stream(self, audio_generator) -> AsyncIterator[str]:
        buffer = []
        for chunk in audio_generator:
            audio_data = np.frombuffer(chunk, dtype=np.int16).astype(np.float32) / 32768.0
            buffer.append(audio_data)
            if len(buffer) > 60:
                full_audio = np.concatenate(buffer)
                buffer = []
                if self.model:
                    segments, _ = self.model.transcribe(full_audio, beam_size=5)
                    text = " ".join([s.text for s in segments])
                    if text.strip(): yield text.strip()
                else:
                    yield "Mocked transcription: Hello"
