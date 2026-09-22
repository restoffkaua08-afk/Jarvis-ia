import asyncio
import os
from unittest.mock import MagicMock, AsyncMock
from openjarvis.os.voice_pipeline import VoicePipeline
from openjarvis.os.providers.base import LLMProvider, VoiceProvider, STTProvider

# Mock Providers para teste de integração sem depender de Hardware/API keys no momento do teste
class MockLLM(LLMProvider):
    async def generate(self, messages, tools=None):
        tokens = ["Olá, ", "eu ", "sou ", "a ", "Sexta-Feira. ", "Como ", "posso ", "ajudar?"]
        for t in tokens:
            await asyncio.sleep(0.1)
            yield t
    async def generate_complete(self, messages, tools=None):
        return MagicMock(text="Olá, eu sou a Sexta-Feira.")

class MockVoice(VoiceProvider):
    async def synthesize_stream(self, text):
        print(f"[TTS-Mock] Synthesizing: {text}")
        yield b"audio_chunk_1"
        yield b"audio_chunk_2"

class MockSTT(STTProvider):
    async def transcribe_stream(self, audio_generator):
        yield "Olá Sexta-Feira, tudo bem?"

async def main():
    print("--- [TESTE V2] Iniciando Pipeline de Voz ---")
    
    # Mocking PyAudio to avoid hardware errors in CLI environment
    import unittest.mock as mock
    with mock.patch('pyaudio.PyAudio'), \
         mock.patch('pyaudio.PyAudio.open'):
        
        pipeline = VoicePipeline(MockLLM(), MockVoice(), MockSTT())
        
        print("\n1. Testando Fluxo de Resposta e Buffering...")
        # We manually trigger a response instead of listen_and_respond to control the flow
        history = []
        # Simulate the LLM -> TTS loop
        full_response = ""
        phrase_buffer = ""
        
        async for token in pipeline.llm.generate(history):
            full_response += token
            phrase_buffer += token
            if any(p in token for p in [".", "!", "?", "\n"]):
                print(f"[Buffer] Sending phrase to TTS: {phrase_buffer}")
                await pipeline._speak_phrase(phrase_buffer)
                phrase_buffer = ""
        
        print(f"Resposta Final: {full_response}")

        print("\n2. Testando Barge-in (Interrupção)...")
        # Start a long response task
        task = asyncio.create_task(pipeline._process_response(history))
        await asyncio.sleep(0.2)
        
        print("[System] Triggering Barge-in now!")
        pipeline.trigger_barge_in()
        
        try:
            await task
        except asyncio.CancelledError:
            print("✅ Sucesso: Tarefa do LLM foi cancelada pelo Barge-in.")
        except Exception as e:
            print(f"❌ Erro inesperado: {e}")

    print("\n--- Teste V2 Concluído ---")

if __name__ == "__main__":
    asyncio.run(main())
