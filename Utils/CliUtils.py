from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from datetime import datetime


def printBanner(console: Console):
    console.print(Panel(banner), justify="center", style="magenta")
    console.print()

def printSetupSteps(console: Console):
    console.print(steps, style=styleTypes.prompt)

def getPrompt(name):
    with open(f"Prompts/{name}.txt") as f:
        return f.read()

def getUserPrompt(console: Console, prompt="Your prompt"):
    console.print(f"[bold green]{prompt}>[/bold green] ", end="", style=styleTypes.userTag)
    return console.input("")

def printMsgLLM(console: Console, text):
    console.print(f"\n\n[bold]LLM>[/bold] ", style=styleTypes.llm, end="")
    md = Markdown(text) if text is not None else ""
    console.print(md)
    console.print("\n")

banner = r"""
    _______. _______ .___  ___.  __    __  .______          ___       __  
    /       ||   ____||   \/   | |  |  |  | |   _  \        /   \     |  | 
   |   (----`|  |__   |  \  /  | |  |  |  | |  |_)  |      /  ^  \    |  | 
    \   \    |   __|  |  |\/|  | |  |  |  | |      /      /  /_\  \   |  | 
.----)   |   |  |____ |  |  |  | |  `--'  | |  |\  \----./  _____  \  |  | 
|_______/    |_______||__|  |__|  \______/  | _| `._____/__/     \__\ |__| 

[bold]Software Emulation & Reversing AI Agent[/bold]                                                           
"""

steps = r"""
[bold]Setup steps:[/bold]
1. Ensure that you have Ghidra running, with the binary of interest loaded.
2. Ensure that the Ghidra bridge extension is running in your Ghidra instance.
3. Ensure that you have the ghidraMCP plugin installed and enabled in your Ghidra instance.
[bold]For more information, do check out the README file.[/bold]
"""


# Colour definitions
class styleTypes:
    info = "cyan"
    warning = "magenta"
    error = "red bold"
    prompt = "white"
    userTag = "green bold"
    llm = "yellow"

def isCommand(inp, validOptions):
    return inp.strip().lower() in validOptions

def writeLog(modelName, session):
    with Console(file=open(f"Logs/SEmuRAI_ChatDump_{datetime.now().strftime("%H-%M-%S_%Y-%m-%d")}.log", "w+")) as f:
                f.print(f"MODEL: {modelName}\n\n")
                f.print(session.history)