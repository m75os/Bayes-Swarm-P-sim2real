# Assumes you have the following packages:
#   - ros-humble-gazebo
#   - ros-humble-cartographer
#   - ros-humble-cartographer-ros
#   - ros-humble-navigation2
#   - ros-humble-nav2-bringup
#
# The turtlebot3 and turtlebot3_msgs are found in the ROBOTIS_Packages directory
# within this repository
#
# Assumes you have the xfce4-terminal environment
#
# If script not working, setup ROS Gazebo package with instructions from:
#   https://emanual.robotis.com/docs/en/platform/turtlebot3/simulation/

# For starting gazebo simulation
export ROS_DOMAIN_ID=30 # For Turtlebot3
export TURTLEBOT3_MODEL=burger # Must get turtlebot model before starting simulation 
source /usr/share/gazebo/setup.sh # Must source simulation setup for gazebo to start properly
source /opt/ros/humble/setup.bash
source ~/Bayes-Swarm-P-sim2real/ros2_packages/install/setup.bash
ros2 launch turtlebot3_gazebo empty_world.launch.py  & # Start empty gazebo environment

sleep 5

# For driving turtlebot in gazebo
export ROS_DOMAIN_ID=30
export TURTLEBOT3_MODEL=burger
source /opt/ros/humble/setup.bash
source ~/Bayes-Swarm-P-sim2real/ros2_packages/install/setup.bash
ros2 run turtlebot3_teleop teleop_keyboard


