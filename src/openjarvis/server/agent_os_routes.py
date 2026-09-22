from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException, Depends
from fastapi import Request
from typing import List, Any, Optional
import json
import logging

from openjarvis.os.harness import VerificationHarness
from openjarvis.tools.windows_tools import LaunchAppTool, WriteFileTool, ReadFileTool
from openjarvis.os.voice_pipeline import VoicePipeline
from openjarvis.os.providers.llm_provider import OllamaProvider
from openjarvis.os.providers.voice_provider import ElevenLabsProvider
from openjarvis.os.providers.stt_provider import LocalSTTProvider

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/agent-os", tags=["Agent OS"])

# Global state for the voice pipeline (singleton for the server process)
_voice_pipeline: Optional[VoicePipeline] = None

def get_voice_pipeline(request: Request):
    global _voice_pipeline
    if _voice_pipeline is None:
        # Initialize providers
        llm = OllamaProvider()
        voice = ElevenLabsProvider()
        stt = LocalSTTProvider()
        _voice_pipeline = VoicePipeline(llm, voice, stt)
    return _voice_pipeline

@router.post("/execute")
async def execute_command(request: Request, payload: dict):
    """
    Executes an OS command through the Verification Harness.
    Payload example: {"tool": "launch", "args": {"app_path": "notepad.exe"}}
    """
    tool_type = payload.get("tool")
    args = payload.get("args", {})
    
    harness = VerificationHarness()
    
    if tool_type == "launch":
        tool = LaunchAppTool()
    elif tool_type == "write":
        tool = WriteFileTool()
    elif tool_type == "read":
        tool = ReadFileTool()
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported tool: {tool_type}")
    
    result = harness.verify_tool(tool, **args)
    return {
        "status": result.status.name,
        "output": result.output,
        "error": result.error
    }

@router.websocket("/voice")
async def voice_websocket(websocket: WebSocket, request: Request):
    """
    Real-time voice interaction via WebSocket.
    Handles audio streaming and barge-in triggers.
    """
    await websocket.accept()
    pipeline = get_voice_pipeline(request)
    history = []
    
    try:
        while True:
            data = await websocket.receive_json()
            
            # Handle control messages
            if data.get("type") == "barge_in":
                pipeline.trigger_barge_in()
                await websocket.send_json({"type": "system", "content": "Interrupted"})
                continue
                
            # Handle audio chunks (binary data sent as base64 or similar in JSON)
            if data.get("type") == "audio":
                # In a full implementation, we'd stream this to the STT provider
                # For now, we'll simulate a trigger for the demo
                pass
                
            # Handle text commands sent via voice interface
            if data.get("type") == "text":
                text = data.get("content", "")
                history.append({"role": "user", "content": text})
                
                # Stream response back to client
                async for token in pipeline.llm.generate(history):
                    await websocket.send_json({"type": "token", "content": token})
                    
    except WebSocketDisconnect:
        logger.info("Voice WebSocket disconnected")
    except Exception as e:
        logger.error(f"Voice WebSocket error: {e}")
        await websocket.send_json({"type": "error", "content": str(e)})
