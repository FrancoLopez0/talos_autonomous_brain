ros2 topic pub -1 /llm_prompt std_msgs/msg/String "{data: 'Eres el cerebro de un robot. Podrias mover el motor izquierdo a la posicion de 20 grados?.'}"
ros2 run  autonomous_rover_brain langchain_node
colcon build
source /opt/ros/jazzy/setup.bash

