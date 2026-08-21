#!/usr/bin/env bash

set -eo pipefail

source /opt/ros/jazzy/setup.bash
source "$HOME/motor_comm_jazzy_ws/install/setup.bash"

set -u

export ROS_DOMAIN_ID=17
export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
export ROS_AUTOMATIC_DISCOVERY_RANGE=SUBNET
export CYCLONEDDS_URI="file://$HOME/.config/motor_comm/cyclonedds_station.xml"

unset ROS_LOCALHOST_ONLY
unset ROS_STATIC_PEERS
unset ROS_PEER_IP

STATION_PORT="/dev/serial/by-id/usb-STMicroelectronics_STM32_STLink_066EFF495177514867222628-if02"

if [[ ! -e "$STATION_PORT" ]]; then
    echo "Situation STM not found:"
    echo "$STATION_PORT"
    exit 1
fi

exec ros2 run motor_comm station_node \
    --ros-args \
    -p port:="$STATION_PORT"
