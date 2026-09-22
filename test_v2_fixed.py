import sys
import os
import asyncio
from unittest.mock import MagicMock, AsyncMock

# Set project root
src_path = r"C:\Users\SextaFeira\Jarvis-ia\src"
if src_path not in sys.path:
    sys.path.append(src_path)

try:
    from openjarvis.os.voice_pipeline import VoicePipeline
    from openjarvis.os.providers.base import LLMProvider, VoiceProvider, STTProvider
    print("✅ Imports successful!")
except ImportError as e:
    print(f"❌ Import failed: {e}")
    sys.exit(1)

class MockLLM(LLMProvider):
    async def generate(self, messages, tools=None):
        tokens = ["Olá, ", "eu ", "sou ", "a ", "Sexta-Feira. ", "Posso ", "ajudar?"]
        for t in tokens:
            await asyncio.sleep(0.1)
            yield t
    async def generate_complete(self, messages, tools=None):
        return MagicMock(text="Olá")

class MockVoice(VoiceProvider):
    async def synthesize_stream(self, text):
        print(f"[TTS-Mock] Synthesizing phrase: {text}")
        yield b"audio_chunk"

class MockSTT(STTProvider):
    async def transcribe_stream(self, audio_generator):
        yield "Olá Sexta-Feira"

async def main():
    print("\n--- [TEST V2] Voice Pipeline Integration ---")
    
    import unittest.mock as mock
    with mock.patch('pyaudio.PyAudio'), mock.patch('pyaudio.PyAudio.open'):
        pipeline = VoicePipeline(MockLLM(), MockVoice(), MockSTT())
        
        print("\n1. Testing Phrase Buffering...")
        history = []
        full_res = ""
        phrase_buf = ""
        async for token in pipeline.llm.generate(history):
            full_res += token
            phrase_buf += token
            if any(p in token for p in [".", "!", "?", "\n"]):
                print(f"Buffer Triggered -> Sending: {phrase_buf}")
                await pipeline._speak_phrase(phrase_buf)
                phrase_buf = ""
        
        print(f"Final Response: {full_res}")

        print("\n2. Testing Barge-in Logic...")
        task = asyncio.create_task(pipeline._process_response(history))
        await asyncio.sleep(0.2)
        print("[System] Interrupting...")
        pipeline.trigger_barge_in()
        
        try:
            await task
        except asyncio.CancelledError:
            print("✅ Success: LLM task cancelled by Barge-in.")
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
