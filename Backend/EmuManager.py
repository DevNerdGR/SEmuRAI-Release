from __future__ import annotations
"""
Makes use of Qiling emulaton framework
"""
from qiling import *
from qiling.extensions import pipe
import lief
from lief import Binary, ELF, MachO, PE
import os
import io

class RootFS:
    _base = "/../Resources/QilingRootFsTemplates/"
    x8664_linux_rootFS = _base + "x8664_linux_glibc2.39/"
    arm_linux_rootFS = _base + "arm_linux/"
    x8664_windows_rootFS = _base + "x8664_windows/"
    x8664_macos_rootFS = _base + "x8664_macos/"


class QilingSession:
    def __init__(self, pathToBinary: str, ghidraBaseAddr: int, args: list=[]):
        bin = lief.parse(pathToBinary)
        
        if bin.format == Binary.FORMATS.ELF:
            arch = bin.header.machine_type
            if arch == lief.ELF.ARCH.X86_64:
                rfs = RootFS.x8664_linux_rootFS
                print("AAY")
            elif arch == lief.ELF.ARCH.ARM or arch == lief.ELF.ARCH.AARCH64:
                rfs = RootFS.arm_linux_rootFS
                print("YAY")
            else:
                raise Exception("Binary format unknown!")
        elif bin.format == Binary.FORMATS.MACHO:
            rfs = RootFS.x8664_macos_rootFS
        elif bin.format == Binary.FORMATS.PE:
            rfs = RootFS.x8664_windows_rootFS
        else:
            raise Exception("Binary format unknown!")
        

        self.ql = Qiling(
            [pathToBinary] + args,
            rootfs=os.path.dirname(os.path.abspath(__file__)) + rfs
        )
        self.ghidraBase = ghidraBaseAddr
        self.hookedAddrs = dict()
        self.outStream = pipe.SimpleOutStream(0)
        self.ql.os.stdout = self.outStream
        self.ql.os.stdin = pipe.SimpleInStream(0)
        self.firstRun = True

        
    
    def ghidraToQilingAddress(self, ghidraAddress):
        return ghidraAddress - self.ghidraBase + self.ql.loader.images[0].base

    def qilingToGhidraAddress(self, qilingAddress):
        return qilingAddress - self.ql.loader.images[0].base + self.ghidraBase

    def setBreakpoint(self, qilingAddr, handler=None):
        if handler == None:
            handler = QilingSession.genericHandler
        hook = self.ql.hook_address(handler, qilingAddr)
        self.hookedAddrs.update({qilingAddr : hook})
    
    def removeBreakpoint(self, qilingAddr):
        self.ql.hook_del(self.hookedAddrs[qilingAddr])
        self.hookedAddrs.pop(qilingAddr)

    def getBreakpoints(self):
        return set([hex(self.qilingToGhidraAddress(a)) for a in list(self.hookedAddrs.keys())])

    def genericHandler(ql: Qiling):
        ql.emu_stop()

    def setPC(self, qilingAddr):
        self.ql.arch.regs.arch_pc = qilingAddr
    
    def getPC(self):
        return self.qilingToGhidraAddress(self.ql.arch.regs.arch_pc)
    
    def runTillBreak(self, timeout_us=5e+6):
        try:
            if self.firstRun:
                self.ql.run(timeout=int(timeout_us))
                self.firstRun = False
            else:
                self.step()
                self.ql.emu_start(begin=self.ql.arch.regs.arch_pc, end=0xFFFFFFFFFFFFFFFF, timeout=int(timeout_us))
            
            return (True, self.getPC())
        except Exception as e:
            return (False, str(e))

    def step(self):
        if self.ql.arch.regs.arch_pc in list(self.hookedAddrs.keys()):
            addr = self.ql.arch.regs.arch_pc
            self.removeBreakpoint(addr)
            self.ql.emu_start(begin=self.ql.arch.regs.arch_pc, end=0xFFFFFFFFFFFFFFFF, count=1)
            self.setBreakpoint(addr)
        else:
            self.ql.emu_start(begin=self.ql.arch.regs.arch_pc, end=0xFFFFFFFFFFFFFFFF, count=1)

    def readRegister(self, reg: str):
        return self.ql.arch.regs.read(reg)
    
    def writeRegister(self, reg: str, value: int):
        self.ql.arch.regs.write(reg, value)
    
    def readMem(self, addr: int, length: int):
        return self.ql.mem.read(addr, length).hex()
    
    def writeMem(self, addr: int, data: bytes):
        self.ql.mem.write(addr, data)

    def getStdout(self):
        return self.outStream.read()
    
