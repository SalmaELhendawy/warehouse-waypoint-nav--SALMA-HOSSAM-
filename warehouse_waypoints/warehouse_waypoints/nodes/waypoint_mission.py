#!/usr/bin/env python3
"""Home -> Loading (wait 30 s) -> Storage -> Shipping -> Home, with RViz markers."""
import math
import sys
import time

import rclpy
from geometry_msgs.msg import PoseStamped
from nav2_simple_commander.robot_navigator import BasicNavigator, TaskResult
from rclpy.parameter import Parameter
from rclpy.qos import (QoSProfile, DurabilityPolicy, ReliabilityPolicy,
                       HistoryPolicy)
from std_msgs.msg import ColorRGBA
from visualization_msgs.msg import Marker, MarkerArray

# name, x, y, yaw (map frame, radians). Index 0 = Home.
WAYPOINTS = [
    ('Charging Station (Home)', 0.00, 0.00, 0.00),
    ('Loading Station',         3.50, 0.00, 0.00),
    ('Storage Area',            12.00, 2.10, 0.00),
    ('Shipping Station',        9.00, -1.50, 0.00),
]

# Mission order (indexes into WAYPOINTS) and wait time (seconds) after arriving.
ORDER = [1, 2, 3, 0]
WAIT_AT = {1: 30.0}

BLUE = ColorRGBA(r=0.0, g=0.3, b=1.0, a=1.0)
GREEN = ColorRGBA(r=0.0, g=1.0, b=0.0, a=1.0)
BLACK = ColorRGBA(r=0.0, g=0.0, b=0.0, a=1.0)


def make_pose(nav, x, y, yaw):
    pose = PoseStamped()
    pose.header.frame_id = 'map'
    pose.header.stamp = nav.get_clock().now().to_msg()
    pose.pose.position.x = float(x)
    pose.pose.position.y = float(y)
    pose.pose.orientation.z = math.sin(yaw / 2.0)
    pose.pose.orientation.w = math.cos(yaw / 2.0)
    return pose


def make_marker(ns, mid, mtype, x, y, z, yaw, scale, color, text=''):
    m = Marker()
    m.header.frame_id = 'map'
    m.ns = ns
    m.id = mid
    m.type = mtype
    m.action = Marker.ADD
    m.pose.position.x = float(x)
    m.pose.position.y = float(y)
    m.pose.position.z = float(z)
    m.pose.orientation.z = math.sin(yaw / 2.0)
    m.pose.orientation.w = math.cos(yaw / 2.0)
    m.scale.x, m.scale.y, m.scale.z = scale
    m.color = color
    m.text = text
    return m


def with_alpha(color, a):
    return ColorRGBA(r=color.r, g=color.g, b=color.b, a=a)


def make_markers(active):
    """Pin-shaped marker per waypoint: floor ring + stem + head (+ glow halo
    when active) + heading arrow + name label. Active = green, others = blue."""
    arr = MarkerArray()
    for i, (name, x, y, yaw) in enumerate(WAYPOINTS):
        is_active = (i == active)
        color = GREEN if is_active else BLUE

        # Ring on the floor
        arr.markers.append(make_marker(
            'ring', i, Marker.CYLINDER, x, y, 0.01, 0.0,
            (0.5, 0.5, 0.02), with_alpha(color, 0.5)))
        # Stem
        arr.markers.append(make_marker(
            'stem', i, Marker.CYLINDER, x, y, 0.175, 0.0,
            (0.04, 0.04, 0.35), color))
        # Head
        arr.markers.append(make_marker(
            'head', i, Marker.SPHERE, x, y, 0.45, 0.0,
            (0.15, 0.15, 0.15), color))
        # Glow halo (visible only for the active goal)
        arr.markers.append(make_marker(
            'glow', i, Marker.SPHERE, x, y, 0.45, 0.0,
            (0.5, 0.5, 0.5), with_alpha(color, 0.3 if is_active else 0.0)))
        # Heading arrow on the floor
        arr.markers.append(make_marker(
            'heading', i, Marker.ARROW, x, y, 0.05, yaw,
            (0.5, 0.08, 0.08), color))
        # Name label above the pin
        arr.markers.append(make_marker(
            'label', i, Marker.TEXT_VIEW_FACING, x, y, 0.9, 0.0,
            (0.0, 0.0, 0.4), BLACK, text=name))
    return arr


def main():
    rclpy.init()
    nav = BasicNavigator()
    nav.set_parameters([Parameter('use_sim_time', Parameter.Type.BOOL, True)])

    qos = QoSProfile(depth=1, history=HistoryPolicy.KEEP_LAST,
                     reliability=ReliabilityPolicy.RELIABLE,
                     durability=DurabilityPolicy.TRANSIENT_LOCAL)
    marker_pub = nav.create_publisher(MarkerArray, '/waypoint_markers', qos)

    def publish_markers(active):
        marker_pub.publish(make_markers(active))

    publish_markers(0)                          # Home is green at the start

    # Mission starts only after Nav2 + AMCL are active and the robot is
    # localized at the Charging Station (Home).
    home = WAYPOINTS[0]
    nav.setInitialPose(make_pose(nav, home[1], home[2], home[3]))
    nav.info('[MISSION] Waiting for Nav2 and AMCL to become active...')
    nav.waitUntilNav2Active(navigator='bt_navigator', localizer='amcl')
    nav.info('[MISSION] Start: Home -> Loading (30 s) -> Storage -> Shipping -> Home')

    try:
        for step, idx in enumerate(ORDER, start=1):
            name, x, y, yaw = WAYPOINTS[idx]
            publish_markers(idx)                # active goal green, others blue
            nav.info(f'[GOAL {step}/{len(ORDER)}] Heading to {name} '
                     f'(x={x:.2f}, y={y:.2f})')
            nav.goToPose(make_pose(nav, x, y, yaw))

            last = 0.0
            while not nav.isTaskComplete():
                fb = nav.getFeedback()
                if fb and time.time() - last > 5.0:
                    nav.info(f'  distance remaining: {fb.distance_remaining:.2f} m')
                    last = time.time()

            result = nav.getResult()
            if result != TaskResult.SUCCEEDED:
                publish_markers(None)
                nav.error(f'[FAILED] Goal "{name}" at (x={x:.2f}, y={y:.2f}) '
                          f'ended with result: {result.name}. Mission stopped.')
                rclpy.shutdown()
                sys.exit(1)

            nav.info(f'[OK] Reached {name}')

            if idx in WAIT_AT:
                secs = WAIT_AT[idx]
                nav.info(f'[WAIT] Waiting {secs:.0f} s at {name}')
                start = nav.get_clock().now()
                next_print = 10.0
                while True:
                    elapsed = (nav.get_clock().now() - start).nanoseconds / 1e9
                    if elapsed >= secs:
                        break
                    if elapsed >= next_print:
                        nav.info(f'  waited {elapsed:.0f}/{secs:.0f} s')
                        next_print += 10.0
                    rclpy.spin_once(nav, timeout_sec=0.1)

        publish_markers(None)                   # arrived home: all markers blue
        nav.info('[MISSION COMPLETE] Robot is back at the Charging Station (Home)')
    except KeyboardInterrupt:
        nav.warn('[MISSION] Interrupted, cancelling current goal')
        nav.cancelTask()

    rclpy.shutdown()


if __name__ == '__main__':
    main()