import rclpy
from rclpy.node import Node
from std_msgs.msg import String
from langchain_openrouter import ChatOpenRouter
from langchain.agents import create_agent
from langchain_core.messages import HumanMessage
from autonomous_rover_brain.tools.ros2_service_tool import SetWheelPositionTool
import os


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

        print("=" * 20)
        print(ia_model)
        print(max_tokens)
        print(temperature)
        print("=" * 20)

        self.set_wheel_position = SetWheelPositionTool(node=self)

        tools = [self.set_wheel_position._run]

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

        try:
            messages = [HumanMessage(content=prompt_text)]
            response = self.agent.invoke({"messages": messages})

            response_msg = String()
            response_msg.data = response["messages"][-1].content
            self.publisher_.publish(response_msg)

            self.get_logger().info(f"Respuesta publicada: '{response["messages"][-1].content}...'")

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
