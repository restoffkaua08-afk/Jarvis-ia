import os
import asyncio
import pyaudio
import numpy as np
from typing import AsyncIterator, Optional, List, Any
from .providers.base import LLMProvider, VoiceProvider, STTProvider

class VoicePipeline:
    def __init__(self, llm: LLMProvider, voice: VoiceProvider, stt: STTProvider, sample_rate: int = 16000, chunk_size: int = 512):
        self.llm = llm
        self.voice = voice
        self.stt = stt
        self.sample_rate = sample_rate
        self.chunk_size = chunk_size
        self.p = pyaudio.PyAudio()
        self.stream_in = self.p.open(format=pyaudio.paInt16, channels=1, rate=self.sample_rate, input=True, frames_per_buffer=self.chunk_size)
        self.stream_out = self.p.open(format=pyaudio.paInt16, channels=1, rate=24000, output=True, frames_per_buffer=self.chunk_size)
        self._interrupt_requested = False
        self._current_task: Optional[asyncio.Task] = None

    async def listen_and_respond(self, history: List[Any]):
        print("[Sexta-Feira] Listening...")
        async for text in self.stt.transcribe_stream(self._audio_generator()):
            if not text: continue
            print(f"[User]: {text}")
            history.append({"role": "user", "content": text})
            self._current_task = asyncio.create_task(self._process_response(history))
            await self._current_task

    async def _process_response(self, history: List[Any]):
        full_response = ""
        phrase_buffer = ""
        try:
            async for token in self.llm.generate(history):
                if self._interrupt_requested: return
                full_response += token
                phrase_buffer += token
                if any(p in token for p in [".", "!", "?", "\n"]):
                    await self._speak_phrase(phrase_buffer)
                    phrase_buffer = ""
            if phrase_buffer: await self._speak_phrase(phrase_buffer)
            history.append({"role": "assistant", "content": full_response})
        except asyncio.CancelledError: pass

    async def _speak_phrase(self, text: str):
        if not text.strip(): return
        async for audio_chunk in self.voice.synthesize_stream(text):
            if self._interrupt_requested: return
            self.stream_out.write(audio_chunk)

    def _audio_generator(self):
        while True:
            yield self.stream_in.read(self.chunk_size, exception_on_overflow=False)

    def trigger_barge_in(self):
        self._interrupt_requested = True
        if self._current_task: self._current_task.cancel()
        print("[System] Barge-in triggered.")
        self._interrupt_requested = False

    def close(self):
        self.stream_in.close()
        self.stream_out.close()
        self.p.terminate()
