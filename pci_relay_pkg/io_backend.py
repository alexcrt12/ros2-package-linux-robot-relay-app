import os
import sys
import ctypes
import subprocess

# Define paths for the auto-generated C extension
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
C_SOURCE_PATH = os.path.join(BASE_DIR, 'hw_io.c')
LIB_PATH = os.path.join(BASE_DIR, 'hw_io.so')

def _ensure_hw_lib():
    """Compiles a tiny C wrapper for the inline assembly outl/inl macros if it doesn't exist."""
    if not os.path.exists(LIB_PATH):
        print("Compiling native hardware I/O wrapper...")
        c_code = """
        #include <sys/io.h>
        #include <stdint.h>

        int setup_io(void) { 
            return iopl(3); 
        }

        void write_outl(uint32_t val, uint16_t port) { 
            outl(val, port); 
        }

        uint32_t read_inl(uint16_t port) { 
            return inl(port); 
        }
        """
        with open(C_SOURCE_PATH, 'w') as f:
            f.write(c_code)

        try:
            subprocess.run(['gcc', '-shared', '-o', LIB_PATH, '-fPIC', C_SOURCE_PATH], check=True)
            print("Wrapper compiled successfully.")
        except FileNotFoundError:
            raise RuntimeError("gcc is not installed. Please install 'build-essential' to compile the I/O wrapper.")
        except subprocess.CalledProcessError:
            raise RuntimeError("Failed to compile the hardware I/O wrapper.")


# Compile the wrapper automatically on first run
_ensure_hw_lib()

# Load the compiled library
try:
    hw_lib = ctypes.CDLL(LIB_PATH)
    hw_lib.setup_io.restype = ctypes.c_int
    hw_lib.write_outl.argtypes = [ctypes.c_uint, ctypes.c_ushort]
    hw_lib.read_inl.argtypes = [ctypes.c_ushort]
    hw_lib.read_inl.restype = ctypes.c_uint
except Exception as e:
    raise RuntimeError(f"Could not load custom hardware I/O library: {e}")


class IoBackend:
    def __init__(self, bdf: str):
        self.bdf = bdf
        self._enable_device(bdf)
        self.io_base = self._read_bar1_base(bdf)

        # Give this process native access to hardware ports
        if hw_lib.setup_io() != 0:
            raise PermissionError("Accessing hardware I/O requires root privileges. Run with sudo.")

    def write_reg(self, offset: int, value: int) -> None:
        port_address = self.io_base + offset
        # True 32-bit atomic write natively executed on the CPU
        hw_lib.write_outl(value, port_address)

    def read_reg(self, offset: int) -> int:
        port_address = self.io_base + offset
        # True 32-bit atomic read natively executed on the CPU
        return hw_lib.read_inl(port_address)

    @staticmethod
    def _enable_device(bdf: str) -> None:
        enable_path = f"/sys/bus/pci/devices/{bdf}/enable"
        try:
            with open(enable_path, 'r+') as f:
                content = f.read().strip()
                if content != '1':
                    f.seek(0)
                    f.write('1')
        except FileNotFoundError:
            raise FileNotFoundError(f"PCI device '{bdf}' not found at {enable_path}")
        except PermissionError:
            raise PermissionError("Enabling a PCI device requires root privileges. Run with sudo.")

    @staticmethod
    def _read_bar1_base(bdf: str) -> int:
        resource_path = f"/sys/bus/pci/devices/{bdf}/resource"
        try:
            with open(resource_path, 'r') as f:
                lines = f.readlines()
                if len(lines) < 2:
                    raise ValueError(f"Device {bdf} does not appear to have a BAR1.")
                bar1_line = lines[1]
                base_str = bar1_line.split()[0]
                return int(base_str, 16)
        except FileNotFoundError:
            raise FileNotFoundError(f"Resource file for {bdf} not found at {resource_path}")