from setuptools import find_packages, setup

package_name = 'warehouse_waypoints'

setup(
    name=package_name,
    version='0.0.1',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='toqa',
    maintainer_email='todo@todo.todo',
    description='Autonomous warehouse waypoint mission with RViz markers',
    license='Apache-2.0',
    entry_points={
        'console_scripts': [
            'waypoint_mission = warehouse_waypoints.nodes.waypoint_mission:main',
        ],
    },
)