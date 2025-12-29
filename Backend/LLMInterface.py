# TODO: IMPLEMENT ASYNC RESOURCE CLEANUP

import asyncio
import os
import json
import time
from rich import print
from dotenv import load_dotenv
from openai import OpenAI, RateLimitError
from openai.types.chat.chat_completion import Choice
from contextlib import AsyncExitStack
from typing import Optional
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from abc import ABC, abstractmethod


class AnalysisSession(ABC):
    @abstractmethod
    def __init__(self, api_key, endpoint, modelName):
        pass
    
    @abstractmethod
    def sendMessage(self):
        pass
    


class SimpleAnalysisSession(AnalysisSession):
    def __init__(self, api_key, endpoint, modelName):
        load_dotenv()
        super().__init__(api_key, endpoint, modelName)
        #print(api_key)
        self.asyncLoop = asyncio.new_event_loop()
        self.client = OpenAI(api_key=api_key, base_url=endpoint)
        self.modelName = modelName
        self.history = []
        self.emuSession = MCPClientSession("Backend/SemuraiMCPServer.py", command="fastmcp", preargs=["run"], args=["--no-banner", "--log-level", "CRITICAL"], loop=self.asyncLoop)
        self.ghidraSession = MCPClientSession(os.getenv("GHIDRA_MCP_SERVER_PATH"), loop=self.asyncLoop)

        self.emuSession.tools
    
    def sendMessage(self, prompt, role="user", handleToolcalls:bool=True) -> Choice:
        try:
            self.history.append({
                "role": role,
                "content": prompt
            })
            response = self.client.chat.completions.create(
                model=self.modelName,
                messages=self.history,
                tools=self.emuSession.tools + self.ghidraSession.tools
            )
            self.history.append({
                "role": Roles.assistant,
                "content": response.choices[0].message.content if response.choices[0].message.content is not None else "" 
            })

            if handleToolcalls and (response.choices[0].message.tool_calls is not None):
                for call in response.choices[0].message.tool_calls:
                    name = call.function.name
                    args = json.loads(call.function.arguments)

                    if name in self.emuSession.toolNames:
                        res = self.asyncLoop.run_until_complete(self.emuSession.session.call_tool(name, args))
                    elif name in self.ghidraSession.toolNames:
                        res = self.asyncLoop.run_until_complete(self.ghidraSession.session.call_tool(name, args))
                    else:
                        res = DummyContent(name) # Represents invalid tool calls

                    self.history.append({
                        "role": Roles.system, #Roles.toolResult, # CHANGED FOR COMPATIBILITY WITH OPENAI MODELS!
                        "content": f"Call to {name} | Result: {res.content}"
                    })
                    return self.sendMessage("Tool call done.", role=Roles.system, handleToolcalls=True) # Enable recursive tool calling
            return response.choices[0].message.content if response.choices[0].message is not None else ""
        except RateLimitError:
            print("Rate limit error. Sleeping for 1 minute and retrying.")
            time.sleep(60)
            return self.sendMessage(prompt, role, handleToolcalls)

class StaticOnlyAnalysisSession(AnalysisSession):
    def __init__(self, api_key, endpoint, modelName):
        load_dotenv()
        super().__init__(api_key, endpoint, modelName)
        #print(api_key)
        self.asyncLoop = asyncio.new_event_loop()
        self.client = OpenAI(api_key=api_key, base_url=endpoint)
        self.modelName = modelName
        self.history = []
        self.ghidraSession = MCPClientSession(os.getenv("GHIDRA_MCP_SERVER_PATH"), loop=self.asyncLoop)

    
    def sendMessage(self, prompt, role="user", handleToolcalls:bool=True) -> Choice:
        try:
            self.history.append({
                "role": role,
                "content": prompt
            })
            response = self.client.chat.completions.create(
                model=self.modelName,
                messages=self.history,
                tools=self.ghidraSession.tools
            )
            self.history.append({
                "role": Roles.assistant,
                "content": response.choices[0].message.content if response.choices[0].message.content is not None else "" 
            })

            if handleToolcalls and (response.choices[0].message.tool_calls is not None):
                for call in response.choices[0].message.tool_calls:
                    name = call.function.name
                    args = json.loads(call.function.arguments)

                    if name in self.ghidraSession.toolNames:
                        res = self.asyncLoop.run_until_complete(self.ghidraSession.session.call_tool(name, args))
                    else:
                        res = DummyContent(name) # Represents invalid tool calls

                    self.history.append({
                        "role": Roles.system, #Roles.toolResult, # CHANGED FOR COMPATIBILITY WITH OPENAI MODELS!
                        "content": f"Call to {name} | Result: {res.content}"
                    })
                    return self.sendMessage("Tool call done.", role=Roles.system, handleToolcalls=True) # Enable recursive tool calling
            return response.choices[0].message.content if response.choices[0].message is not None else ""
        except RateLimitError:
            print("Rate limit error. Sleeping for 1 minute and retrying.")
            time.sleep(60)
            return self.sendMessage(prompt, role, handleToolcalls)
    

class MCPClientSession:
    def __init__(self, serverPath, loop, command="python3", preargs=list(), args=list()):
        self.session: Optional[ClientSession] = None
        self.exitStack = AsyncExitStack()
        self.loop = loop
        self.loop.run_until_complete(self.connect(serverPath, command, preargs=preargs, args=args))

    async def connect(self, serverPath, command, preargs=[], args:list=[]):
        serverParams = StdioServerParameters(
            command=command,
            args= preargs + [serverPath] + args,
            env=None
        )
        stdioTransport = await self.exitStack.enter_async_context(stdio_client(serverParams))
        self.stdio, self.write = stdioTransport
        self.session = await self.exitStack.enter_async_context(ClientSession(self.stdio, self.write))

        await self.session.initialize()

        response = await self.session.list_tools()
        rawTools = response.tools
        #print("\nConnected to server with tools:", [tool.name for tool in rawTools])
        
        # Convert schema
        self.tools = []
        self.toolNames = [] # For convenience
        for tool in rawTools:
            self.tools.append({
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description or "",
                    "parameters": tool.inputSchema
                }
            })
            self.toolNames.append(tool.name)

class DummyContent:
    def __init__(self, toolName):
        self.content = f"Invalid call to tool {toolName}. Tool unavailable/does not exist."

class Roles:
    system = "system"
    user = "user"
    assistant = "assistant"
    #orchestratorAssistant = "assistant (orchestrator)"
    #staticAnalysisAssistant = "assistant (static analysis expert)"
    #dynamicAnalysisAssistant = "assistant (dynamic analysis/emulation expert)"
    toolResult = "tool"


