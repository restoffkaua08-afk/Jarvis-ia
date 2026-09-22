from dataclasses import dataclass
from enum import Enum, auto
from typing import Any, Optional

class VerificationStatus(Enum):
    SUCCESS = auto()
    FAILURE = auto()
    UNKNOWN = auto()

@dataclass
class ToolResult:
    output: str
    status: VerificationStatus
    error: Optional[str] = None

class VerificationHarness:
    @staticmethod
    def verify_tool(tool: Any, *args, **kwargs) -> ToolResult:
        try:
            output = tool.execute(*args, **kwargs)
            success, msg = tool.verify(*args, **kwargs)
            if success:
                return ToolResult(output=output, status=VerificationStatus.SUCCESS)
            else:
                return ToolResult(output=output, status=VerificationStatus.FAILURE, error=f"Verification failed: {msg}")
        except Exception as e:
            return ToolResult(output="", status=VerificationStatus.FAILURE, error=f"Execution error: {str(e)}")
