from abc import ABC, abstractmethod
from typing import AsyncIterator, List, Any, Optional
from dataclasses import dataclass

@dataclass
class LLMResponse:
    text: str
    tool_calls: Optional[List[Any]] = None
    raw_response: Any = None

class LLMProvider(ABC):
    @abstractmethod
    async def generate(self, messages: List[Any], tools: Optional[List[Any]] = None) -> AsyncIterator[str]:
        pass
    @abstractmethod
    async def generate_complete(self, messages: List[Any], tools: Optional[List[Any]] = None) -> LLMResponse:
        pass

class VoiceProvider(ABC):
    @abstractmethod
    async def synthesize_stream(self, text: str) -> AsyncIterator[bytes]:
        pass

class STTProvider(ABC):
    @abstractmethod
    async def transcribe_stream(self, audio_generator) -> AsyncIterator[str]:
        pass
