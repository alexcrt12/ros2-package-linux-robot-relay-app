from enum import Enum, auto
from dataclasses import dataclass
from pci_relay_pkg.io_backend import IoBackend


class Port(Enum):
    P1A = auto()
    P1B = auto()
    P1C = auto()
    P2A = auto()
    P2B = auto()
    P2C = auto()


class Dir(Enum):
    Input = auto()
    Output = auto()


@dataclass
class PortInfo:
    data_off: int
    dir_off: int
    byte_index: int
    dir_bit: int


class Pci2321:
    def __init__(self, bdf: str = "0000:05:01.0"):
        self._io = IoBackend(bdf)

        # Read the CURRENT state from hardware into shadow memory
        # This prevents accidental overwrites if a relay was left on from a crash
        self._shadow_regs = {
            0x00: self._io.read_reg(0x00),
            0x04: self._io.read_reg(0x04),
            0x10: self._io.read_reg(0x10),
            0x14: self._io.read_reg(0x14)
        }

    @staticmethod
    def _port_mapping(port: Port) -> PortInfo:
        mapping = {
            Port.P1A: PortInfo(0x00, 0x04, 0, 0),
            Port.P1B: PortInfo(0x00, 0x04, 1, 1),
            Port.P1C: PortInfo(0x00, 0x04, 2, 2),
            Port.P2A: PortInfo(0x10, 0x14, 0, 0),
            Port.P2B: PortInfo(0x10, 0x14, 1, 1),
            Port.P2C: PortInfo(0x10, 0x14, 2, 2),
        }
        return mapping.get(port, PortInfo(0x00, 0x00, 0, 0))

    def configure_port(self, port: Port, direction: Dir) -> None:
        info = self._port_mapping(port)

        # Read from SHADOW memory, not hardware
        reg = self._shadow_regs[info.dir_off]

        if direction == Dir.Output:
            reg |= (1 << info.dir_bit)
        else:
            reg &= ~(1 << info.dir_bit) & 0xFFFFFFFF

        # Save to SHADOW memory and write to hardware
        self._shadow_regs[info.dir_off] = reg
        self._io.write_reg(info.dir_off, reg)

    def write_channel(self, port: Port, bit: int, on: bool) -> None:
        info = self._port_mapping(port)
        bitpos = info.byte_index * 8 + bit  # Position in the 32-bit register

        # Read from SHADOW memory, not hardware
        reg = self._shadow_regs[info.data_off]

        if on:
            reg |= (1 << bitpos)
        else:
            reg &= ~(1 << bitpos) & 0xFFFFFFFF

        # Save to SHADOW memory and write to hardware
        self._shadow_regs[info.data_off] = reg
        self._io.write_reg(info.data_off, reg)

    def write_port(self, port: Port, value: int) -> None:
        info = self._port_mapping(port)
        shift = info.byte_index * 8

        # Read from SHADOW memory, not hardware
        reg = self._shadow_regs[info.data_off]

        # MODIFY
        # Clear the 8 bits at the target position
        reg &= ~(0xFF << shift) & 0xFFFFFFFF
        # Set the new value (masked to 8 bits to match uint8_t cast)
        reg |= (value & 0xFF) << shift

        # Save to SHADOW memory and write to hardware
        self._shadow_regs[info.data_off] = reg
        self._io.write_reg(info.data_off, reg)

    def read_port(self, port: Port) -> int:
        info = self._port_mapping(port)
        shift = info.byte_index * 8

        # For reading, we DO want to query the actual hardware pins
        reg = self._io.read_reg(info.data_off)

        # EXTRACT
        value = (reg >> shift) & 0xFF
        return value
