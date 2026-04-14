import rclpy
from rclpy.node import Node
from std_msgs.msg import String
from langchain_openrouter import ChatOpenRouter
from langchain.agents import create_agent
from langchain_core.messages import HumanMessage, SystemMessage
from autonomous_rover_brain.tools.ros2_service_tool import SetWheelPositionTool
from ament_index_python.packages import get_package_share_directory
import os
import threading


def read_prompt(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read()


class LangchainNode(Node):
    def __init__(self):
        super().__init__("langchain_node")

        self.subscription = self.create_subscription(
            String, "/llm_prompt", self.prompt_callback, 10
        )
        self.publisher_ = self.create_publisher(String, "/llm_response", 10)

        self.declare_parameter("model", "google/gemini-2.5-flash")
        self.declare_parameter("max_tokens", 1024)

        ia_model = self.get_parameter("model").get_parameter_value().string_value

        max_tokens = (
            self.get_parameter("max_tokens").get_parameter_value().integer_value
        )

        temperature = 0.7

        package_share_dir = get_package_share_directory("autonomous_rover_brain")

        file_path = os.path.join(package_share_dir, "config/prompts", "system.md")

        self.system_prompt = SystemMessage(read_prompt(file_path))

        self.messages = [self.system_prompt]

        self.set_wheel_position = SetWheelPositionTool(
            node=self, service_name="talos/set_wheel_position"
        )

        tools = [self.set_wheel_position]

        api_key = os.getenv("OPENROUTER_API_KEY")
        if not api_key:
            self.get_logger().error(
                "No se encontró OPENROUTER_API_KEY en las variables de entorno."
            )

        self.get_logger().info("Inicializando modelo Langchain (OpenAI)...")

        self.llm = ChatOpenRouter(
            model=ia_model,
            temperature=temperature,
            max_tokens=max_tokens,
            max_retries=0,
        )
        self.agent = create_agent(model=self.llm, tools=tools)

        self.get_logger().info(
            "Nodo Langchain inicializado y esperando prompts en /llm_prompt."
        )

    def prompt_callback(self, msg):
        prompt_text = msg.data
        self.get_logger().info(f"Recibido prompt: '{prompt_text}'")

        thread = threading.Thread(target=self._process_llm, args=(prompt_text,))
        thread.start()

    def _process_llm(self, prompt_text):
        """Esta función corre en un hilo separado y no bloquea a ROS 2"""
        try:
            self.messages.append(HumanMessage(content=prompt_text))

            response = self.agent.invoke({"messages": self.messages})

            if "tool_call" in response:
                for tool_call in response.tool_calls:
                    self.get_logger().info(
                        f"Tool: {tool_call['name']} | Args: {tool_call['args']}"
                    )

            ai_message = response["messages"][-1]

            self.messages.append(ai_message)

            self.get_logger().info(f"Respuesta publicada: '{ai_message.content}'")

            response_msg = String()
            response_msg.data = ai_message.content
            self.publisher_.publish(response_msg)

        except Exception as e:
            self.get_logger().error(f"Error procesando con Langchain: {e}")


def main(args=None):
    rclpy.init(args=args)
    node = LangchainNode()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
