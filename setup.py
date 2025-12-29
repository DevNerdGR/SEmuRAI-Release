import argparse
import subprocess
import sys
from pathlib import Path

parser = argparse.ArgumentParser(
    prog="SEmuRAI Setup",
    description="Script to set up SEmuRAI."
)

parser.add_argument("--no-dependencies", action="store_true")
parser.add_argument("--break-system-packages", action="store_true")

args = parser.parse_args()


if not args.no_dependencies:
    print("===== Dependencies installation =====")
    cmd = [sys.executable, "-m", "pip", "install", "-r", "requirements.txt", "--break-system-packages"] if args.break_system_packages else [sys.executable, "-m", "pip", "install", "-r", "requirements.txt"]
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
    print("===== Done. =====\n\n")

print("===== .env setup =====")
if not (Path(".env").exists() and input(".env file detected. Override? (y/n) ").strip().lower() == "N"):
    apikey = input("LLM API key: ").strip()
    endpoint = input("LLM endpoint (base URL): ").strip()
    modelName = input("Desired LLM model name: ").strip()
    ghidraMCPPath = input("Path to Ghidra MCP Server (absolute path): ").strip

    with open(".env", "w") as f:
        f.write(f"LLM_API_KEY={apikey}\n")
        f.write(f"LLM_ENDPOINT={endpoint}\n")
        f.write(f"LLM_MODEL_NAME={modelName}\n")
        f.write(f"GHIDRA_MCP_SERVER_PATH={ghidraMCPPath}")
print("===== Done. =====")
