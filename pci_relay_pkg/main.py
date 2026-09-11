import sys
import time
import rclpy
from rclpy.node import Node
from std_msgs.msg import String
from dataclasses import dataclass
from pci_relay_pkg import pci2321

@dataclass
class Relay:
    port: pci2321.Port
    bit: int
    name: str

POWER  = Relay(pci2321.Port.P2A, 5, "POWER")
BRAKE1 = Relay(pci2321.Port.P1C, 4, "BRAKE 1")
BRAKE2 = Relay(pci2321.Port.P1C, 5, "BRAKE 2")
BRAKE3 = Relay(pci2321.Port.P1C, 6, "BRAKE 3")
BRAKE4 = Relay(pci2321.Port.P1C, 7, "BRAKE 4")

class HardwareController(Node):
    def __init__(self):
        super().__init__('hardware_controller')
        self.board = pci2321.Pci2321()
        
        self.get_logger().info("Configuring hardware ports...")
        self.board.configure_port(pci2321.Port.P1A, pci2321.Dir.Output)
        self.board.configure_port(pci2321.Port.P1B, pci2321.Dir.Output)
        self.board.configure_port(pci2321.Port.P1C, pci2321.Dir.Output) 
        self.board.configure_port(pci2321.Port.P2A, pci2321.Dir.Output) 
        
        self.reset_all_ports()
        self.get_logger().info("Hardware ready. Listening on /relay_cmd")
        self.get_logger().info("Publish 'start' to run the original sequence.")

        # Listen for string commands to trigger the sequence
        self.subscription = self.create_subscription(
            String, 'relay_cmd', self.command_callback, 10
        )

    def reset_all_ports(self):
        self.board.write_port(pci2321.Port.P1A, 0)
        self.board.write_port(pci2321.Port.P1B, 0)
        self.board.write_port(pci2321.Port.P1C, 0)
        self.board.write_port(pci2321.Port.P2A, 0)

    def command_callback(self, msg: String):
        cmd = msg.data.lower().strip()  # .strip() removes hidden spaces/newlines

    def run_original_sequence(self):
        """Recreates your exact ETAPA B sequential startup"""
        self.get_logger().info("Starting original sequential startup...")
        
        self.get_logger().info("Pornire POWER...")
        self.board.write_channel(POWER.port, POWER.bit, True)
        time.sleep(2)

        self.get_logger().info("Pornire BRAKE 1...")
        self.board.write_channel(BRAKE1.port, BRAKE1.bit, True)
        time.sleep(2)

        self.get_logger().info("Pornire BRAKE 2...")
        self.board.write_channel(BRAKE2.port, BRAKE2.bit, True)
        time.sleep(2)

        self.get_logger().info("Pornire BRAKE 3...")
        self.board.write_channel(BRAKE3.port, BRAKE3.bit, True)
        time.sleep(2)

        self.get_logger().info("Pornire BRAKE 4...")
        self.board.write_channel(BRAKE4.port, BRAKE4.bit, True)
        time.sleep(2)

        self.get_logger().info("POWER + 4 BRAKES active. Publish 'stop' to end test.")

    def stop_sequence(self):
        """Recreates your exact ETAPA B shutdown sequence"""
        self.get_logger().info("Oprire test...")
        
        self.board.write_channel(BRAKE1.port, BRAKE1.bit, False)
        self.board.write_channel(BRAKE2.port, BRAKE2.bit, False)
        self.board.write_channel(BRAKE3.port, BRAKE3.bit, False)
        self.board.write_channel(BRAKE4.port, BRAKE4.bit, False)
        time.sleep(2)

        self.board.write_channel(POWER.port, POWER.bit, False)
        self.reset_all_ports()
        self.get_logger().info("Toate porturile au fost resetate la 0.")

def main(args=None):
    rclpy.init(args=args)
    node = None
    try:
        node = HardwareController()
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    except Exception as e:
        sys.stderr.write(f"Fatal error: {e}\n")
    finally:
        # Safety catch: Force ports to 0 on crash or exit
        if node:
            try:
                node.reset_all_ports()
                node.get_logger().info("Ports safely reset to 0 during shutdown.")
            except:
                pass
            node.destroy_node()
        rclpy.try_shutdown()

if __name__ == '__main__':
    main()
