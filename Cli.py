#!/usr/bin/env python3
# Cli.py

# TODO: FIX (REMOVE) MCP SERVER LOGS OUTPUT, ADD LOADING ICON WHEN WAITING FOR REPLY
import argparse
import os
import readline
from pathlib import Path
from dotenv import load_dotenv
from Utils.CliUtils import styleTypes as st
from Utils.CliUtils import *
from rich.console import Console
from rich.panel import Panel
from Backend.LLMInterface import SimpleAnalysisSession
from Backend.LLMInterface import Roles



parser = argparse.ArgumentParser(description="SEmuRAI — Software Emulation & Reversing AI Agent")
parser.add_argument("--pretty", type=bool, default=True, help="If set as false, ASCII art and banners will not be printed.")
args = parser.parse_args()

cs = Console()

printBanner(cs) if args.pretty else None


load_dotenv()

apiKey, endpoint, modelName = None, None, None
try:
    cs.print("Loading .env variables...", style=st.info)
    apiKey = os.getenv("LLM_API_KEY")
    endpoint = os.getenv("LLM_ENDPOINT")
    modelName = os.getenv("LLM_MODEL_NAME")
    if apiKey is None or endpoint is None or modelName is None:
        raise Exception("Failed to load .env, one or more fields absent")
    cs.print("Load .env variables ok.", style=st.info)
except Exception as e:
    cs.print("Unable to load .env variables!", style=st.warning)
    apiKey = cs.input("Enter API key: ").strip() if apiKey is None else True
    endpoint = cs.input("Enter endpoint: ").strip() if endpoint is None else True
    modelName = cs.input("Enter model name: ").strip() if modelName is None else True

printSetupSteps(cs)
binaryPath = Path(cs.input("Please enter the full path of the target binary: "))
if (not(binaryPath.exists() and  binaryPath.is_file())) and (str(binaryPath) != "d"):
    cs.print("Invalid path! Program exiting.", style=st.error)
    exit(1)
cs.print("Agent ready.\n", style=st.info)

session = SimpleAnalysisSession(apiKey, endpoint, modelName)



# Initial context setting
printMsgLLM(cs, session.sendMessage(getPrompt("initContextSemurai").format(binaryPath, getUserPrompt(cs, "Your instructions for this task")), role=Roles.system, handleToolcalls=False))
try:
    while True:
        inp = getUserPrompt(cs)
        if isCommand(inp, ["q", "quit"]): 
            exit()
        elif isCommand(inp, ["dd", "dump-debug"]):
            cs.print(session.history, style=st.error)
            cs.print("\n\n")
        elif isCommand(inp, ["wd", "write-dump"]):
            writeLog(modelName, session)
        else:
            res = session.sendMessage(inp)
            printMsgLLM(cs, res) if res is not None else cs.print("\nTool call done\n", style=st.info)
except Exception as e:
    writeLog(modelName, session)
    cs.print("Error encountered:", style=st.error)
    cs.print(e)
except KeyboardInterrupt:
    writeLog(modelName, session)
    cs.print("Keyboard interrupt.", style=st.error)