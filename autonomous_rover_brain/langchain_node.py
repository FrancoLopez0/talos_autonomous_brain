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


IA_MODEL = "google/gemini-2.5-flash"
MAX_TOKENS = 1024
TEMPERATURE = 0.7
MAX_RETRIES = 0

TOPIC_PROMPT = "/llm_prompt"
TOPIC_PUBLISH = "/llm_response"


class LangchainNode(Node):
    def __init__(self):
        super().__init__("langchain_node")

        self.subscription = self.create_subscription(
            String, TOPIC_PROMPT, self.prompt_callback, 10
        )
        self.publisher_ = self.create_publisher(String, TOPIC_PUBLISH, 10)

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
            model=IA_MODEL,
            temperature=TEMPERATURE,
            max_tokens=MAX_TOKENS,
            max_retries=MAX_RETRIES,
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
