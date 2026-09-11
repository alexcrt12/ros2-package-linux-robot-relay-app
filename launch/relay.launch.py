from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([
        Node(
            package='pci_relay_pkg',
            executable='relay_node',
            name='hardware_controller',
            output='screen',          # Ensures print statements appear in the terminal
            emulate_tty=True          # Retains colored log output
        )
    ])
