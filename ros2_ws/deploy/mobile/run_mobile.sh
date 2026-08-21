#!/usr/bin/env bash

set -eo pipefail

source /opt/ros/jazzy/setup.bash
source "$HOME/ICT/ros2_ws/install/setup.bash"

set -u

export ROS_DOMAIN_ID=17
export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
export ROS_AUTOMATIC_DISCOVERY_RANGE=SUBNET
export CYCLONEDDS_URI="file://$HOME/.config/motor_comm/cyclonedds_mobile.xml"

unset ROS_LOCALHOST_ONLY
unset ROS_STATIC_PEERS
unset ROS_PEER_IP

MOBILE_PORT="/dev/serial/by-id/usb-STMicroelectronics_STM32_STLink_0668FF485753667187215421-if02"

if [[ ! -e "$MOBILE_PORT" ]]; then
    echo "Mobile STM not found:"
    echo "$MOBILE_PORT"
    exit 1
fi

exec ros2 run motor_comm mobile_node \
    --ros-args \
    -p port:="$MOBILE_PORT"
