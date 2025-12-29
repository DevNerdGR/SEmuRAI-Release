from fastmcp import FastMCP
import ghidra_bridge
from EmuManager import QilingSession
from EmuManager import RootFS
import logging
import os
import codecs


mcp = FastMCP(name="SEmuRAI (Qiling Backend)")

bridge = None
emuSession = None


@mcp.tool
def greet(name : str) -> str:
    """Sanity check"""
    return f"Hello, {name}!! :))"

@mcp.tool
def setupEmulator(pathToBinary: str, mainFunctionAddr: str):
    """
    RUN THIS BEFORE ANY EMULATION WORK!
    Running this will also cause emulation session to reset.

    - pathToBinary argument refers to the absolute path referencing the binary loaded in ghidra on the user's system (not your, AI agent's, mounted disk). If in doubt, prompt the user for it.
    - mainFunctionAddr refers to the address of the main function. Make sure address starts with 0x.
    """
    try:
        global bridge
        global emuSession

        bridge = ghidra_bridge.GhidraBridge(namespace=globals())
        
        currentProgram = bridge.remote_eval("currentProgram") # Sanity check

        if currentProgram is None:
            return "No program currently loaded in Ghidra"
        
        emuSession = QilingSession(pathToBinary, int(currentProgram.getImageBase().toString(), 16))

        emuSession.setBreakpoint(emuSession.ghidraToQilingAddress(int(mainFunctionAddr, 16)))
        res = emuSession.runTillBreak()
        if res[0]:
            pc = hex(res[1])
        
        return f"Emulator session set up. PC at main function ({pc})"
    except Exception as e:
        return f"Error: {str(e)}"

@mcp.tool
def getCurrentProgramName() -> str:
    """Get name of current loaded program, second sanity check"""
    global bridge
    try:
        if bridge is None:
            return "Setup required before usage. Run setupEmulator()"
        return bridge.remote_eval("currentProgram.getName()")
    except Exception as e:
        return f"Error connecting to Ghidra: {str(e)}"

@mcp.tool
def readRegister(registerName : str, astype:str="raw"):
    """Reads the value in the specified register.
    astype argument specifies if the returned value is represented as a raw value ("raw") pointer value ("addr").
    """
    global bridge
    global emuSession
    try:
        if bridge is None or emuSession is None:
            return "Setup required before usage. Run setupEmulator()"
        return (hex(emuSession.qilingToGhidraAddress(emuSession.readRegister(registerName))) if astype == "addr" else emuSession.readRegister(registerName))
    except Exception as e:
        return f"Error: {str(e)}"

@mcp.tool
def writeRegister(value : int, registerName : str) -> None:
    """Writes the value in the specified register. Take note of endianess."""
    global bridge
    global emuSession
    try:
        if bridge is None or emuSession is None:
            return "Setup required before usage. Run setupEmulator()"
        emuSession.writeRegister(registerName, value)
    except Exception as e:
        return f"Error: {str(e)}"

@mcp.tool
def readMemory(startAddress : str, length : int) -> str:
    """Reads n number of bytes (specified by length parameter) from startAddress. Make sure startAddress starts with 0x. Bytes read are parsed and returned as a hex string."""
    global bridge
    global emuSession
    try:
        if bridge is None or emuSession is None:
            return "Setup required before usage. Run setupEmulator()"
        return emuSession.readMem(emuSession.ghidraToQilingAddress(int(startAddress, 16)), length)
    except Exception as e:
        return f"Error: {str(e)}"

# @mcp.tool
# def readNullTerminatedString(startAddress : str, maxLength=100) -> str:
#     """Reads bytes up to n bytes (specified by maxLength parameter) or when null character is read, whichever is ealier, from startAddress. Bytes are converted to characters and subsequently a string. Make sure startAddress starts with 0x."""
#     global bridge
#     global emuHelper
#     try:
#         if bridge is None or emuHelper is None:
#             return "Setup required before usage. Run setupEmulator()"
#         currentProgram = bridge.remote_eval("currentProgram")
#         addressFactory = currentProgram.getAddressFactory()
#         addr = addressFactory.getAddress(startAddress)

#         return emuHelper.readNullTerminatedString(addr, maxLength)

#     except Exception as e:
#         return f"Error connecting to Ghidra: {str(e)}"

@mcp.tool
def writeMemory(startAddress : str, bytesToWrite : str) -> None:
    """Write bytes (specified by bytesToWrite in hex string format) from startAddress onwards. Make sure startAddress starts with 0x. Bytes must be supplied as hex string, without 0x in front."""
    global bridge
    global emuSession
    try:
        if bridge is None or emuSession is None:
            return "Setup required before usage. Run setupEmulator()"
        
        byteStr = bytes.fromhex(bytesToWrite)
        emuSession.writeMem(emuSession.ghidraToQilingAddress(int(startAddress, 16)), byteStr)

    except Exception as e:
        return f"Error: {str(e)}"

@mcp.tool
def setBreakpoint(address : str) -> None:
    """Establishes a breakpoint at the specified address. Make sure address starts with 0x"""
    global bridge
    global emuSession
    try:
        if bridge is None or emuSession is None:
            return "Setup required before usage. Run setupEmulator()"
        emuSession.setBreakpoint(emuSession.ghidraToQilingAddress(int(address, 16)))
    except Exception as e:
        return f"Error: {str(e)}"

@mcp.tool
def removeBreakpoint(address : str) -> None:
    """Removes breakpoint at the specified address. Make sure address starts with 0x"""
    global bridge
    global emuSession
    try:
        if bridge is None or emuSession is None:
            return "Setup required before usage. Run setupEmulator()"
        emuSession.removeBreakpoint(emuSession.ghidraToQilingAddress(int(address, 16)))
    except Exception as e:
        return f"Error: {str(e)}"

@mcp.tool
def getBreakpoints() -> list:
    """Returns set containing addresses of breakpoints."""
    global bridge
    global emuSession
    try:
        if bridge is None or emuSession is None:
            return "Setup required before usage. Run setupEmulator()"
        return list(emuSession.getBreakpoints())
    except Exception as e:
        return f"Error connecting to Ghidra: {str(e)}"

# @mcp.tool
# def stepInstruction() -> None:
#     """Steps emulation by one instruction. To make this meaningful, ensure that memory/registers and breakpoints are set up."""
#     global bridge
#     global emuHelper
#     try:
#         if bridge is None or emuHelper is None:
#             return "Setup required before usage. Run setupEmulator()"
#         tm = bridge.remote_import("ghidra.util.task.TaskMonitor")
#         emuHelper.step(tm.DUMMY)
#     except Exception as e:
#         return f"Error connecting to Ghidra: {str(e)}"


@mcp.tool
def run() -> str:
    """Starts emulation from address pointed to by program counter/instruction pointer. Will stop when breakpoint hit. To make this meaningful, ensure that memory/registers and breakpoints are set up."""
    global bridge
    global emuSession
    try:
        if bridge is None or emuSession is None:
            return "Setup required before usage. Run setupEmulator()"
        res = emuSession.runTillBreak()
        if res[0]:
            return f"PC at {hex(res[1])}"
        else:
            return f"Emulation failed.\n{res[1]}"
    except Exception as e:
        return f"Error: {str(e)}"


# @mcp.tool
# def getLastError() -> str:
#     """Diagnostic function that provides information if emulation fails"""
#     global bridge
#     global emuHelper
#     try:
#         if bridge is None or emuHelper is None:
#             return "Setup required before usage. Run setupEmulator()"
#         return emuHelper.getLastError()
#     except Exception as e:
#         return f"Error connecting to Ghidra: {str(e)}"

@mcp.tool
def hexToDecimal(hexValue : str) -> int:
    """Converts hexadecimal value into its decimal representation. Hexadecimal value must start with 0x. Use this whenever you need to do a conversion, do not do it on your own."""
    if not hexValue.startswith("0x"):
        return "Argument needs to start with 0x"
    return int(hexValue.replace("0x", "").strip(), 16)

@mcp.tool
def setPC(address : str) -> None:
    """Sets the program counter/instruction pointer to address specified by address argument. Make sure address starts with 0x"""
    global bridge
    global emuSession
    try:
        if bridge is None or emuSession is None:
            return "Setup required before usage. Run setupEmulator()"
        emuSession.setPC(emuSession.ghidraToQilingAddress(int(address, 16)))
    except Exception as e:
        return f"Error: {str(e)}"

@mcp.tool
def getPC() -> str:
    """Gets the value in the program counter/instruction pointer, returned as a hex value."""
    global bridge
    global emuSession
    try:
        if bridge is None or emuSession is None:
            return "Setup required before usage. Run setupEmulator()"
        return hex(emuSession.getPC())
    except Exception as e:
        return f"Error: {str(e)}"

@mcp.tool
def readStdout() -> str:
    """Read stdout stream."""
    global bridge
    global emuSession
    try:
        if bridge is None or emuSession is None:
            return "Setup required before usage. Run setupEmulator()"
        return str(emuSession.getStdout())
    except Exception as e:
        return f"Error: {str(e)}"



if __name__ == "__main__":
    mcp.run()
