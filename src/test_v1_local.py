import sys
import os
import asyncio

# Force the current directory into sys.path to allow imports from the same folder
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from openjarvis.os.harness import VerificationHarness
from openjarvis.tools.windows_tools import LaunchAppTool, WriteFileTool

def run_test():
    harness = VerificationHarness()
    
    print("\n--- [TESTE 1] Lançar Notepad ---")
    app_tool = LaunchAppTool()
    # No Windows, 'notepad.exe' geralmente está no PATH
    res1 = harness.verify_tool(app_tool, "notepad.exe")
    print(f"Status: {res1.status} | Output: {res1.output}")
    if res1.error: print(f"Erro: {res1.error}")

    print("\n--- [TESTE 2] Escrever Arquivo ---")
    write_tool = WriteFileTool()
    path = "v1_validation_test.txt"
    content = "Sexta-Feira OS - V1 Operacional"
    res2 = harness.verify_tool(write_tool, path, content)
    print(f"Status: {res2.status} | Output: {res2.output}")
    if res2.error: print(f"Erro: {res2.error}")

    print("\n--- [TESTE 3] Falha Determinística (App Falso) ---")
    res3 = harness.verify_tool(app_tool, "fake_app_123.exe")
    print(f"Status: {res3.status} | Output: {res3.output}")
    print(f"Verificação de Erro: {res3.error}")

if __name__ == "__main__":
    run_test()
