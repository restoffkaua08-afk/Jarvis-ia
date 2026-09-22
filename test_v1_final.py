import sys
import os

# Absolute path to the project src folder
src_path = r"C:\Users\SextaFeira\Jarvis-ia\src"
if src_path not in sys.path:
    sys.path.append(src_path)

try:
    from openjarvis.os.harness import VerificationHarness
    from openjarvis.tools.windows_tools import LaunchAppTool, WriteFileTool
    print("Imports successful!")
except ImportError as e:
    print(f"Import failed: {e}")
    sys.exit(1)

def run_tests():
    harness = VerificationHarness()
    
    print("\n--- [TEST 1] Launch Notepad ---")
    app_tool = LaunchAppTool()
    res1 = harness.verify_tool(app_tool, "notepad.exe")
    print(f"Status: {res1.status} | Output: {res1.output}")
    if res1.error: print(f"Error: {res1.error}")

    print("\n--- [TEST 2] Write File ---")
    write_tool = WriteFileTool()
    path = "v1_final_test.txt"
    content = "Sexta-Feira OS - Final Test"
    res2 = harness.verify_tool(write_tool, path, content)
    print(f"Status: {res2.status} | Output: {res2.output}")
    if res2.error: print(f"Error: {res2.error}")

    print("\n--- [TEST 3] Deterministic Failure (Fake App) ---")
    res3 = harness.verify_tool(app_tool, "non_existent_app_999.exe")
    print(f"Status: {res3.status} | Output: {res3.output}")
    print(f"Expected Error: {res3.error}")

if __name__ == "__main__":
    run_tests()
