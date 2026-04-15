ros2 topic pub -1 /llm_prompt std_msgs/msg/String "{data: 'Necesito que me ayudes a cargar este vidrio'}"
ros2 run  autonomous_rover_brain langchain_node
ros2 topic echo /llm_response
colcon build
source /opt/ros/jazzy/setup.bash

colcon build --packages-select robot_interfaces --cmake-args -DPython3_EXECUTABLE=/usr/bin/python3

ros2 run rqt_console rqt_console
