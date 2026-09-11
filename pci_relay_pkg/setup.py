from setuptools import find_packages, setup

package_name = 'pci_relay_pkg'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='rh-robot',
    maintainer_email='rh-robot@todo.todo',
    description='PCI Relay Controller Package',
    license='TODO: License declaration',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'relay_node = pci_relay_pkg.main:main',
            'gui_node = pci_relay_pkg.gui_node:main'
        ],
    },
)
