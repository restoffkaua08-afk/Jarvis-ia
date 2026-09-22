import os
import subprocess
import psutil
import hashlib
from typing import Tuple, List

class WindowsTool:
    def execute(self, *args, **kwargs) -> str:
        raise NotImplementedError
    def verify(self, *args, **kwargs) -> Tuple[bool, str]:
        raise NotImplementedError

class LaunchAppTool(WindowsTool):
    def execute(self, app_path: str) -> str:
        subprocess.Popen([app_path], shell=True)
        return f"Launched application: {app_path}"
    def verify(self, app_path: str, *args, **kwargs) -> Tuple[bool, str]:
        app_name = os.path.basename(app_path).lower()
        for proc in psutil.process_iter(['name']):
            try:
                if proc.info['name'].lower() == app_name:
                    return True, "Process found running."
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return False, f"Process {app_name} not found in process list."

class ListProcessesTool(WindowsTool):
    def execute(self, *args, **kwargs) -> str:
        procs = [p.info['name'] for p in psutil.process_iter(['name'])]
        return "\n".join(procs)
    def verify(self, *args, **kwargs) -> Tuple[bool, str]:
        return True, "Read operation successful."

class ReadFileTool(WindowsTool):
    def execute(self, file_path: str) -> str:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    def verify(self, file_path: str, *args, **kwargs) -> Tuple[bool, str]:
        if os.path.exists(file_path):
            return True, "File exists."
        return False, "File does not exist."

class WriteFileTool(WindowsTool):
    def execute(self, file_path: str, content: str) -> str:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return f"Successfully wrote to {file_path}"
    def verify(self, file_path: str, content: str, *args, **kwargs) -> Tuple[bool, str]:
        if not os.path.exists(file_path):
            return False, "File was not created."
        with open(file_path, 'rb') as f:
            actual_hash = hashlib.sha256(f.read()).hexdigest()
        expected_hash = hashlib.sha256(content.encode('utf-8')).hexdigest()
        if actual_hash == expected_hash:
            return True, "Content hash verified."
        return False, "Content mismatch detected."
