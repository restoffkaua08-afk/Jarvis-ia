import asyncio
from openjarvis.os.harness import VerificationHarness
from openjarvis.tools.windows_tools import LaunchAppTool, WriteFileTool

async def main():
    harness = VerificationHarness()
    
    print("--- Teste 1: Lançar App (Notepad) ---")
    app_tool = LaunchAppTool()
    # Usamos o caminho comum do Windows para o notepad
    res1 = harness.verify_tool(app_tool, "notepad.exe")
    print(f"Resultado: {res1.status} | Output: {res1.output} | Erro: {res1.error}")

    print("\n--- Teste 2: Escrever Arquivo ---")
    write_tool = WriteFileTool()
    content = "Sexta-Feira Agent OS - V1 Validada"
    path = "v1_test_file.txt"
    res2 = harness.verify_tool(write_tool, path, content)
    print(f"Resultado: {res2.status} | Output: {res2.output} | Erro: {res2.error}")

    print("\n--- Teste 3: Falha Proposital (App Inexistente) ---")
    res3 = harness.verify_tool(app_tool, "app_que_nao_existe.exe")
    print(f"Resultado: {res3.status} | Output: {res3.output} | Erro: {res3.error}")

if __name__ == "__main__":
    asyncio.run(main())
