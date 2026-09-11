import sys
import time
import tkinter as tk
from dataclasses import dataclass
from pci_relay_pkg import pci2321

@dataclass(frozen=True)
class Relay:
    port: pci2321.Port
    bit: int
    name: str

POWER  = Relay(pci2321.Port.P2A, 5, "POWER")
BRAKE1 = Relay(pci2321.Port.P1C, 4, "LEFT KNEE")
BRAKE2 = Relay(pci2321.Port.P1C, 5, "RIGHT KNEE")
BRAKE3 = Relay(pci2321.Port.P1C, 6, "LEFT HIP")
BRAKE4 = Relay(pci2321.Port.P1C, 7, "RIGHT HIP")

class HardwareGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("PCI-2321 Relay Controller")
        self.root.geometry("350x350")
        
        # 1. Create the label FIRST so it exists when we try to update it
        self.status_label = tk.Label(root, text="Initializing...", fg="orange", font=("Arial", 10))
        self.status_label.pack(pady=10)

        # Track the state of each relay (False = OFF, True = ON)
        self.relay_states = {
            POWER: False, BRAKE1: False, 
            BRAKE2: False, BRAKE3: False, BRAKE4: False
        }
        
        # Store button widgets so we can dynamically change their color/text later
        self.buttons = {}

        # 2. Now attempt to initialize the hardware
        try:
            self.board = pci2321.Pci2321()
            self.init_hardware()
            self.status_label.config(text="Hardware Ready", fg="green", font=("Arial", 12))
        except Exception as e:
            self.status_label.config(text=f"Hardware Error: {e}", fg="red")
            self.board = None

        # Generate the 5 individual toggle buttons dynamically
        for relay in [POWER, BRAKE1, BRAKE2, BRAKE3, BRAKE4]:
            btn = tk.Button(root, text=f"Turn ON {relay.name}", width=25, height=1)
            # Default arguments in lambda ensure each button captures its specific relay
            btn.config(command=lambda r=relay, b=btn: self.toggle_relay(r, b))
            btn.pack(pady=3)
            self.buttons[relay] = btn

        tk.Button(root, text="Emergency Reset", command=self.reset_ports, bg="red", fg="white", width=25, height=2).pack(pady=5)

    def init_hardware(self):
        self.board.configure_port(pci2321.Port.P1A, pci2321.Dir.Output)
        self.board.configure_port(pci2321.Port.P1B, pci2321.Dir.Output)
        self.board.configure_port(pci2321.Port.P1C, pci2321.Dir.Output) 
        self.board.configure_port(pci2321.Port.P2A, pci2321.Dir.Output) 
        self.reset_ports()

    def reset_ports(self):
        if not self.board: return
        self.board.write_port(pci2321.Port.P1A, 0)
        self.board.write_port(pci2321.Port.P1B, 0)
        self.board.write_port(pci2321.Port.P1C, 0)
        self.board.write_port(pci2321.Port.P2A, 0)

        # Sync the software state and button UI back to OFF
        for relay in self.relay_states:
            self.relay_states[relay] = False
            if relay in self.buttons:
                # FIXED: Replaced "SystemButtonFace" with "lightgray"
                self.buttons[relay].config(bg="lightgray", text=f"Turn ON {relay.name}")
                
        self.status_label.config(text="All ports reset to 0", fg="blue")

    def toggle_relay(self, relay, btn_widget):
        if not self.board: return
        
        new_state = not self.relay_states[relay]
        self.relay_states[relay] = new_state
        
        self.board.write_channel(relay.port, relay.bit, new_state)
        
        if new_state:
            btn_widget.config(bg="lightgreen", text=f"Turn OFF {relay.name}")
        else:
            # FIXED: Replaced "SystemButtonFace" with "lightgray"
            btn_widget.config(bg="lightgray", text=f"Turn ON {relay.name}")
            
        state_text = "ON" if new_state else "OFF"
        self.status_label.config(text=f"{relay.name} turned {state_text}", fg="blue")
        self.root.update()

def main(args=None):
    root = tk.Tk()
    app = HardwareGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
