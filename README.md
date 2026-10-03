Autonomous Warehouse Waypoint Delivery Robot
Robot: TurtleBot3 Burger | ROS 2: Jazzy | Simulator: Gazebo Harmonic | Stack: SLAM Toolbox, AMCL, Nav2.
------------------------------------------------------------------------------------------------------------
1. Project overview and mission:

This project builds an autonomous TurtleBot3 warehouse robot. The robot is spawned inside a Gazebo ETGAH warehouse world, maps the warehouse with SLAM Toolbox, localizes itself on the saved map with AMCL, and navigates with Nav2 through four named warehouse locations.

Mission: the mission begins and ends at the Charging Station (Home).

Start at the Charging Station (Home)
Navigate to the Loading Station
Wait exactly 30 seconds
Navigate to the Storage Area
Navigate to the Shipping Station
Return to the Charging Station (Home)

Each goal is sent only after the previous goal succeeded. If any goal fails, the mission stops and reports the location of the failed goal.

-----------------------------------------------------------------------------------------------------------------
2.## Repository and Package Structure

warehouse-waypoint-nav-[SALMA-HOSSAM]/
├── robot_navigation/
│   ├── config/
│   │   ├── amcl.yaml
│   │   ├── planner_server.yaml
│   │   ├── controller_server.yaml
│   │   ├── behavior_server.yaml
│   │   └── bt_navigator.yaml
│   ├── launch/
│   │   └── nav2_bringup2.launch.py
│   ├── map/
│   │   ├── warehouse_map.yaml
│   │   └── warehouse_map.pgm
│   ├── rviz/
│   │   └── navigation.rviz
│   ├── CMakeLists.txt
│   └── package.xml
├── warehouse_waypoints/
│   ├── resource/
│   │   └── warehouse_waypoints
│   ├── warehouse_waypoints/
│   │   ├── __init__.py
│   │   └── nodes/
│   │       ├── __init__.py
│   │       └── waypoint_mission.py
│   ├── package.xml
│   ├── setup.cfg
│   └── setup.py
├── images/
└── README.md

----------------------------------------------------------------------

3. Workspace build instructions
Inside The Terminal Write Commands below:

```
mkdir -p ~/warehouse_turtlebot3_ws/src
cd ~/warehouse_turtlebot3_ws/src
# copy robot_navigation and warehouse_waypoints from this repository into src/
cd ~/warehouse_turtlebot3_ws
colcon build --packages-select warehouse_slam robot_navigation warehouse_waypoints
source install/setup.bash
```
----------------------------------------------------------------------------------------------------------

4. How to launch TurtleBot3 inside the warehouse world
The simulator is started from the platform UI, or with the warehouse launch file. The TurtleBot3 Burger is spawned at the Charging Station (Home), which is the origin of the map frame.

Also Verify the simulation before doing anything else:
ros2 topic info /clock -v                              
ros2 topic hz /scan                                    
ros2 topic echo /scan --once --field header.frame_id   
ros2 topic echo /odom --once --field child_frame_id    
ros2 run tf2_tools view_frames        

--------------------------------------------------------------------------------------------------------------
5. How to map the warehouse using SLAM Toolbox
 Use Terminal:

  - Terminal 1
   ros2 launch warehouse_slam slam_toolbox.launch.py
   
   - Terminal 2
   rviz2
   
   - Terminal 3
   ros2 run teleop_twist_keyboard teleop_twist_keyboard

SLAM Toolbox configuration highlights: use_sim_time: true, odom_frame: odom, base_frame: base_footprint, map_frame: map, scan_topic: /scan, max_laser_range: 10.0.
Drive through every accessible aisle, explore the walls, corners and open areas, and avoid duplicated walls and large unexplored gaps. Confirm in RViz (Fixed Frame = map) that the robot pose moves correctly on the map and that the TF tree is map -> odom -> base_footprint.

---------------------------------------------------------------------------------------------------------------------

6. How to save the warehouse map
In terminal:
```
ros2 run nav2_map_server map_saver_cli -f warehouse_map
```
This produces both files, which are kept in warehouse_slam/map/:

warehouse_map.yaml (resolution 0.05, origin [-4.941, -6.595, 0])
warehouse_map.pgm 

The saved map is reloaded by the map server and displayed in RViz to confirm it is correct.

-------------------------------------------------------------------------------------------------------------------

7. How to launch and test AMCL localization
AMCL and the map server are started by amcl2.launch.py . SLAM Toolbox must be closed, otherwise both publish map -> odom.
```
ros2 launch robot_navigation amcl2.launch.py
```
Validation:
ros2 lifecycle get /map_server       
ros2 lifecycle get /amcl               
ros2 topic echo /amcl_pose --once     
ros2 run tf2_ros tf2_echo map base_footprint
ros2 run tf2_tools view_frames   

---------------------------------------

In RViz (Fixed Frame = map) the following displays are used: Map, TF, RobotModel, LaserScan and ParticleCloud.

Set the correct initial pose (initial_pose in amcl.yaml, or 2D Pose Estimate).
Confirm the LiDAR scan aligns with the map walls.
Confirm the particle cloud converges around the robot.
Move the robot and verify localization remains stable.
Confirm /amcl_pose updates while the robot moves.
Localization recovery is demonstrated by displacing the pose estimate and correcting it with 2D Pose Estimate.

------------------------------------------------------------------------------------------------------------

8. How to launch the complete Nav2 system
   
nav2_bringup2.launch.py starts: map_server, amcl, planner_server, controller_server, behavior_server, bt_navigator, lifecycle_manager_navigation and RViz (with rviz/navigation.rviz).

In Terminal:

ros2 launch robot_navigation nav2_bringup2.launch.py

Confirm every lifecycle node becomes active:
ros2 lifecycle get /map_server
ros2 lifecycle get /amcl
ros2 lifecycle get /planner_server
ros2 lifecycle get /controller_server
ros2 lifecycle get /behavior_server
ros2 lifecycle get /bt_navigator

---------------------------------------------
Test before automation:

Display the global costmap and local costmap, the global plan and local plan, the robot, the laser scan, the map and the particles.
Set one manual 2D Goal Pose in RViz and confirm the robot plans and reaches the goal safely.
Then send autonomous goal by send_goal.py script.

Confirm /cmd_vel uses geometry_msgs/msg/Twist:
ros2 topic info /cmd_vel

Main Nav2 configuration: DWB local planner (max speed 0.22 m/s, robot_radius: 0.12), NavFn global planner, inflation radius 0.2 m for narrow aisles, costmap laser range 3.5 / 3.0 m while AMCL uses the full 10 m range.

---------------------------------------------------------------------------------------------------------

9. Waypoint names, positions and orientations
All poses are in the map frame (yaw in radians). They are defined in WAYPOINTS at the top of warehouse_waypoints/warehouse_waypoints/nodes/waypoint_mission.py.

| ID   | Name                     | x (m) | y (m) | yaw (rad) | Role                              |
|------|--------------------------|-------|-------|-----------|-----------------------------------|
| HOME | Charging Station (Home)  | 0.00  | 0.00  | 0.00      | Mission start and final destination |
| 01   | Loading Station          | 3.50  | 0.00  | 0.00      | Wait here for 30 seconds          |
| 02   | Storage Area             | 12.00 | 2.10  | 0.00      | Second navigation goal            |
| 03   | Shipping Station         | 9.00  | -1.50 | 0.00      | Third navigation goal             |

--------------------------------------------------------------------------------------------------------------
10. Mission route
  Charging Station (Home) -> Loading Station -> wait 30 s -> Storage Area -> Shipping Station -> Charging Station (Home)

The mission starts only after Nav2 and AMCL are active and the robot is localized at the Charging Station (the node publishes the Home initial pose and waits with waitUntilNav2Active). It then sends one NavigateToPose goal at a time and waits for each Nav2 result before sending the next goal. If a goal fails, the node stops the mission and reports the failed location.

-------------------------------------------
In Terminal:

ros2 launch robot_navigation nav2_bringup2.launch.py

ros2 run warehouse_waypoints waypoint_mission 

--------------------------------------------------------------------------------------------------------------------

11. RViz waypoint-marker behavior:
    The mission node publishes all waypoints as a visualization_msgs/msg/MarkerArray on the /waypoint_markers topic.
1- Each waypoint is drawn as a pin (floor ring, stem and head) with a heading arrow, placed at its stored pose in the map frame.
2-The station name is displayed above every marker.
3-Blue means an inactive waypoint.
4-Green means the active navigation goal. Only the active goal is green, and it also gets a soft glow halo.
5-The MarkerArray is republished every time the active goal changes.

| Moment                          | Home | Loading | Storage | Shipping |
|---------------------------------|------|---------|---------|----------|
| Mission start (waiting for Nav2)| 🟩   | 🟦      | 🟦      | 🟦       |
| Heading to Loading Station      | 🟦   | 🟩      | 🟦      | 🟦       |
| Heading to Storage Area         | 🟦   | 🟦      | 🟩      | 🟦       |
| Heading to Shipping Station     | 🟦   | 🟦      | 🟦      | 🟩       |
| Returning to Home (last goal)   | 🟩   | 🟦      | 🟦      | 🟦       |
| Mission complete (arrived Home) | 🟦   | 🟦      | 🟦      | 🟦       |

 In RViz the WaypointMarkers display (MarkerArray, topic /waypoint_markers, durability Transient Local) is part of navigation.rviz.

 ---------------------------------------------------------------------------------------------------------
 
12. Required terminal output:

  
Output of the mission node (ros2 run warehouse_waypoints waypoint_mission) :
Example:
[INFO] [basic_navigator]: Publishing Initial Pose
[INFO] [basic_navigator]: [MISSION] Waiting for Nav2 and AMCL to become active...
[INFO] [basic_navigator]: Nav2 is ready for use!
[INFO] [basic_navigator]: [MISSION] Start: Home -> Loading (30 s) -> Storage -> Shipping -> Home
[INFO] [basic_navigator]: [GOAL 1/4] Heading to Loading Station (x=3.50, y=0.00)
[INFO] [basic_navigator]: [OK] Reached Loading Station
[INFO] [basic_navigator]: [WAIT] Waiting 30 s at Loading Station
[INFO] [basic_navigator]:   waited 10/30 s
[INFO] [basic_navigator]:   waited 20/30 s
[INFO] [basic_navigator]: [GOAL 2/4] Heading to Storage Area (x=12.00, y=2.10)
[INFO] [basic_navigator]: [OK] Reached Storage Area
[INFO] [basic_navigator]: [GOAL 3/4] Heading to Shipping Station (x=9.00, y=-1.50)
[INFO] [basic_navigator]: [OK] Reached Shipping Station
[INFO] [basic_navigator]: [GOAL 4/4] Heading to Charging Station (Home) (x=0.00, y=0.00)
[INFO] [basic_navigator]: [OK] Reached Charging Station (Home)
[INFO] [basic_navigator]: [MISSION COMPLETE] Robot is back at the Charging Station (Home)

> Real Output Found in Screenshots Section <
While driving, the node also prints the remaining distance every 5 seconds, for example distance remaining: 8.07 m.

-----------------------------------------------------------------------------------------------------------------

13. Problems encountered and their solutions:

| #  | Problem                                                   | Cause                                                                 | Solution                                                                 |
|----|-----------------------------------------------------------|----------------------------------------------------------------------|--------------------------------------------------------------------------|
| 1  | Message Filter dropping message and jumping TF            | Duplicate /clock publisher, use_sim_time missing on some nodes, stale Gazebo processes | One /clock publisher (ros2 topic info /clock -v), use_sim_time: true on every node, kill old gz sim / bridge processes before every restart |
| 2  | TF tree stopped at odom -> base_footprint (no base_link, base_scan) | robot_state_publisher crashed because the URDF began with a stray Markdown line (```xml) | Cleaned the URDF file and verified with view_frames                      |
| 3  | Launch failed with KeyError: TURTLEBOT3_MODEL             | The original TurtleBot3 launch files read the environment variable at import time | Model, URDF and bridge paths are written directly for the Burger          |
| 4  | SLAM and AMCL saw very little in a large warehouse        | Default LiDAR range was only 3 m                                     | LiDAR <max> raised to 10 m in the SDF, with AMCL laser_max_range and SLAM max_laser_range matched |
| 5  | Robot could not pass narrow aisles                        | Large inflation radius blocked the corridors                         | Costmap inflation radius reduced to 0.2 m and costmap laser range kept short (3.5 / 3.0 m) |
| 6  | Failed to make progress in tight aisles                   | movement_time_allowance too short                                    | Nav2 recovery cleared the costmap and the goal succeeded; the allowance was increased |
| 7  | Timed out while waiting for action server to acknowledge goal request | The BT server timeout (20 ms) was too small under CPU load           | default_server_timeout raised to 100 and debug_trajectory_details set to False |
| 8  | Local costmap invisible and colors pale in RViz           | Costmap displays used Volatile durability and identical names and alpha | Set Transient Local, separate names and alpha for the global and local costmaps |
| 9  | /particle_cloud incompatible QoS warning                  | RViz subscribed Reliable, AMCL publishes Best Effort                 | ParticleCloud reliability set to Best Effort                             |
| 10 | Two launch files started the same nodes                   | Localization and Nav2 launch files both started map_server and amcl  | A single nav2_bringup.launch.py starts everything                        |
| 11 | RViz GLSL link result error in the log                    | Software rendering in the cloud instance                             | Cosmetic; the map and displays render correctly                          |
| 12 | Home marker started blue although it is the first location | The initial MarkerArray was published without an active goal         | Initial MarkerArray now publishes Home as active, and all markers return to blue when the mission completes |

----------------------------------------------------------------------------------------------------------
14. Screenshots

Mapping (SLAM Toolbox)

<img width="757" height="299" alt="slam mapping" src="https://github.com/user-attachments/assets/bda8241a-84b9-43fa-8bbf-a1e3bd9f117e" />

Saved warehouse map
<img width="617" height="311" alt="Screenshot 2026-10-03 143640" src="https://github.com/user-attachments/assets/9d82a7c4-51cc-4227-a287-dc2e64d51670" />

Final Map
<img width="476" height="279" alt="map2" src="https://github.com/user-attachments/assets/62eb7013-9005-4e7d-840e-ea1b4b78b44a" />

AMCL localization (scan aligned with the walls, particle cloud converged)
<img width="955" height="326" alt="correct intial pose" src="https://github.com/user-attachments/assets/1328260f-ddbd-423d-bd32-a2bc587c09f7" />

Navigation: global and local costmaps

<img width="359" height="206" alt="nav global costmap" src="https://github.com/user-attachments/assets/275f740f-2ddb-4a7a-a105-c5472d4877f5" />

<img width="312" height="223" alt="local costmap" src="https://github.com/user-attachments/assets/de92c126-0df0-4050-89f4-1320fae5e8a3" />

Navigation: global plan and local plan
<img width="310" height="232" alt="global plan" src="https://github.com/user-attachments/assets/41fd2c06-aeaa-47b6-899b-6c4d908f2a77" />

All named waypoint markers
<img width="364" height="216" alt="stations" src="https://github.com/user-attachments/assets/a5c7c3af-a2ce-4b2b-a887-f5083c167d0f" />

Active goal in green -Other waypoints in blue
<img width="422" height="287" alt="loading station" src="https://github.com/user-attachments/assets/c18eecf5-ab09-4042-b05b-aaf2dda8983d" />

/waypoint_markers topic in RViz
<img width="304" height="213" alt="rviz markers" src="https://github.com/user-attachments/assets/08894101-ad09-45ec-ba59-d08861a36f83" />

----------------------------------------------------------------------------------------------------------
15. Demonstration video

